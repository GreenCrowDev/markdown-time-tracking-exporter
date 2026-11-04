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
        print(tl)

@dataclass
class Line:
    indent: int
    content: str
    line_num: int

def line_create(raw: str, line_num: int) -> Line:
    cursor = 0
    while cursor < len(raw) and raw[cursor] == ' ':
        cursor += 1
    return Line(cursor, raw[cursor:], line_num)

CHECKBOX = "- [ ]"
COLON = ":"

class TokenType(Enum):
    CHECKBOX = auto()
    DATE = auto()
    COLON = auto()
    TEXT = auto()

@dataclass
class Token:
    type: TokenType
    content: str

def line_tokenize(line: Line) -> list[Token] | None:
    tokens: list[Token] = []
    # Check if the line is a day entry.
    if line.content.startswith(CHECKBOX):
        tokens.append(Token(TokenType.CHECKBOX, CHECKBOX))
        s = line.content[len(CHECKBOX):]
        s = s.lstrip()
        # Check if it has date.
        date = extract_date(s)
        if date is None:
            # Malformed: No date.
            return None
        else:
            # Date.
            tokens.append(Token(TokenType.DATE, date))
            s = s[len(date):]
            # Check if it has colon.
            if not s.startswith(COLON):
                # Malformed: No colon.
                return None
            else:
                tokens.append(Token(TokenType.COLON, COLON))
                s = s[len(COLON):]
                s = s.lstrip()
                # Get project name (can be whatever text).
                tokens.append(Token(TokenType.TEXT, s))
    else:
        # No checkbox.
        return None

    return tokens

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

if __name__ == "__main__":
    main()
