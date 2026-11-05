from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto

file_path = Path("test/time_tracking.md")

def main():
    # Read the whole file.
    content = file_path.read_text(encoding="utf-8")

    # Tokenize line by line.
    token_lines: list[list[Token]] = []
    lines = content.splitlines()
    for line_num, l in enumerate(lines, 1):
        line = line_create(l, line_num)
        tokens = line_tokenize(line)
        token_lines.append(tokens)

    for line_num, tl in enumerate(token_lines, 1):
        print(line_num, " ".join(str(token) for token in tl))

@dataclass
class Line:
    content: str
    line_num: int

def line_create(raw: str, line_num: int) -> Line:
    return Line(raw, line_num)

CHECKBOX = "- [ ]"
COLON = ":"
SPACE = " "
BULLET = "- "
HYPHEN = "-"
HASH = "#"

class TokenType(Enum):
    CHECKBOX = auto()
    DATE = auto()
    COLON = auto()
    TEXT = auto()
    INDENT = auto()
    BULLET = auto()
    TIME = auto()
    HYPHEN = auto()

@dataclass
class Token:
    type: TokenType
    content: str

    def __str__(self):
        return self.type.name

def line_tokenize(line: Line) -> list[Token]:
    tokens: list[Token] = []
    s = line.content

    while s:

        # Strip comment from the string.
        hash_index = s.find(HASH)
        if hash_index != -1:
            s = s[:hash_index]
            continue

        # Check if there's indentation and consume it.
        # Indentation only accepts spaces.
        if s.startswith(SPACE):
            cursor = 0
            while cursor < len(s) and s[cursor] == SPACE:
                cursor += 1
            if cursor > 0:
                s = append_and_strip(s, tokens, TokenType.INDENT, s[:cursor])
                continue
        
        # Check checkbox.
        if s.startswith(CHECKBOX):
            s = append_and_strip(s, tokens, TokenType.CHECKBOX, CHECKBOX)
            continue

        # Check bullet.
        if s.startswith(BULLET):
            s = append_and_strip(s, tokens, TokenType.BULLET, BULLET)
            continue

        # Check colon.
        if s.startswith(COLON):
            s = append_and_strip(s, tokens, TokenType.COLON, COLON)
            continue
        
        if s.startswith(HYPHEN):
            s = append_and_strip(s, tokens, TokenType.HYPHEN, HYPHEN)
            continue

        # Check if it has date.
        date = extract_date(s)
        if date is not None:
            s = append_and_strip(s, tokens, TokenType.DATE, date)
            continue

        time = extract_time(s)
        if time is not None:
            s = append_and_strip(s, tokens, TokenType.TIME, time)
            continue

        # End of hard coded symbols.

        s = s.lstrip()

        # Get project name (can be whatever text).
        if len(s) > 0:
            s = append_and_strip(s, tokens, TokenType.TEXT, s)
            break

    return tokens

def append_and_strip(s: str, tokens: list[Token], token_type: TokenType, content: str, strip: bool = True) -> str:
    if not s.startswith(content):
        raise ValueError(f"Expected prefix: {content!r}")
    
    tokens.append(Token(token_type, content))
    ret = s[len(content):]
    if strip:
        ret = ret.lstrip()
    return ret

# Extracts date from a raw string (e.g. "2000-01-01 lorem ipsum" returns "2000-01-01").
def extract_date(raw: str) -> str | None:
    date_format: str = "YYYY-MM-DD"

    if len(raw) < len(date_format):
        return None

    if raw[4] != '-' or raw[7] != '-':
        return None

    year: str = raw[:4]
    month: str = raw[5:7]
    day: str = raw[8:10]
    if not (year.isdigit() and month.isdigit() and day.isdigit()):
        return None

    return raw[:len(date_format)]

# Extracts time from a raw string (e.g. "12:00 lorem ipsum" returns "12:00").
def extract_time(raw:str) -> str | None:
    time_format: str = "HH:mm"

    if len(raw) < len(time_format):
        return None

    if raw[2] != ':':
        return None

    hour: str = raw[:2]
    minute: str = raw[3:5]
    if not (hour.isdigit() and minute.isdigit()):
        return None

    return raw[:len(time_format)]

if __name__ == "__main__":
    main()
