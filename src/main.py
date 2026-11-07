from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import date, time
from openpyxl import Workbook
from openpyxl.styles import Font
from collections.abc import Iterator
import argparse

file_path = Path("test/time_tracking.md")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str, help="Markdown content")
    args = parser.parse_args()

    if args.text:
        content = args.text
    else:
        # Read the whole file.
        content = file_path.read_text(encoding="utf-8")

    # Tokenize line by line.
    token_lines: list[list[Token]] = []
    lines = content.splitlines()
    for line_num, l in enumerate(lines, 1):
        line = line_create(l, line_num)
        tokens = line_tokenize(line)
        token_lines.append(tokens)

    # Debug print tokens.
    # for line_num, tl in enumerate(token_lines, 1):
    #     print(line_num, " ".join(str(token) for token in tl))

    line_entries: list[LineEntry] = []
    line_entries.append(LineEntry(LineType.ROOT))
    for l in token_lines:
        entry = line_parse(l)
        line_entries.append(entry)
        # print(entry)

    ir = parse_document(line_entries)

    # Debug print ir.
    # for p in ir.projects:
    #     print(p)
    #     for t in p.tasks:
    #         print(t)
    #         for i in t.intervals:
    #             print(i)

    spreadsheet_create(ir)

# ============================================================================
# Tokenizer
# ============================================================================

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

# ============================================================================
# Line parser
# ============================================================================

class LineParser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.cursor = 0

    def peek(self, offset: int = 0) -> Token | None:
        index = self.cursor + offset
        if index >= len(self.tokens):
            return None
        return self.tokens[index]

    def consume(self, expected: TokenType) -> Token:
        token = self.peek()

        if token is None or token.type != expected:
            raise ValueError(f"Expected: {expected}")

        self.cursor += 1
        return token

class LineType(Enum):
    ROOT = auto()
    PROJECT = auto()
    TASK = auto()
    TIME = auto()

@dataclass
class ProjectEntry:
    date: date
    name: str

@dataclass
class TaskEntry:
    description: str

@dataclass
class TimeEntry:
    start: time
    end: time

@dataclass
class LineEntry:
    type: LineType
    entry: ProjectEntry | TaskEntry | TimeEntry | None = None

    def __str__(self):
        return self.type.name

def line_parse(tokens: list[Token]) -> LineEntry:
    p = LineParser(tokens)

    stack: list[Token] = []
    stack_append_peek(stack, p)

    if stack[-1].type == TokenType.CHECKBOX:
        return parse_project(p)

    if stack[-1].type == TokenType.INDENT:
        stack_append_peek(stack, p)
        if stack[-1].type == TokenType.BULLET:
            stack_append_peek(stack, p)
            if stack[-1].type == TokenType.TEXT:
                return parse_task(p)
            if stack[-1].type == TokenType.TIME:
                return parse_time(p)

def stack_append_peek(stack: list[Token], p: LineParser):
    stack.append(p.peek(len(stack)))

def parse_project(p: LineParser) -> LineEntry:
    p.consume(TokenType.CHECKBOX)
    date_token = p.consume(TokenType.DATE)
    p.consume(TokenType.COLON)
    name_token = p.consume(TokenType.TEXT)

    date_data = date(*date_str_to_yyyy_mm_dd(date_token.content))
    name_date = name_token.content
    return LineEntry(LineType.PROJECT, ProjectEntry(date_data, name_date))

def parse_task(p: LineParser) -> LineEntry:
    p.consume(TokenType.INDENT)
    p.consume(TokenType.BULLET)
    text_token = p.consume(TokenType.TEXT)

    text_data = text_token.content
    return LineEntry(LineType.TASK, TaskEntry(text_data))

def parse_time(p: LineParser) -> LineEntry:
    p.consume(TokenType.INDENT)
    p.consume(TokenType.BULLET)
    start_time_token = p.consume(TokenType.TIME)
    p.consume(TokenType.HYPHEN)
    end_time_token = p.consume(TokenType.TIME)

    start_data = time(*time_str_to_hh_mm(start_time_token.content))
    end_data = time(*time_str_to_hh_mm(end_time_token.content))
    return LineEntry(LineType.TIME, TimeEntry(start_data, end_data))

# ============================================================================
# Document parser
# ============================================================================

class DocumentParser:
    def __init__(self, entries: list[LineEntry]):
        self.entries = entries
        self.cursor = 0

    def peek(self, offset: int = 0) -> LineEntry | None:
        index = self.cursor + offset
        if index >= len(self.entries):
            return None
        return self.entries[index]

    def consume(self, expected: LineType) -> LineEntry:
        token = self.peek()

        if token is None:
            raise ValueError("Token is None")

        if token.type != expected:
            raise ValueError(f"Expected: {expected}; Found {token.type}")

        self.cursor += 1
        return token

@dataclass
class IRTime:
    entry: TimeEntry

    def __str__(self):
        return str(self.entry.start) + "-" + str(self.entry.end)

@dataclass
class IRTask:
    entry: TaskEntry | None = None
    intervals: list[IRTime] = field(default_factory=list)

    def __str__(self):
        if self.entry is None:
            return "None"
        return self.entry.description

@dataclass
class IRProject:
    entry: ProjectEntry
    tasks: list[IRTask] = field(default_factory=list)

    def __str__(self):
        return str(self.entry.date) + " " + self.entry.name

@dataclass
class IntermediateRepresentation:
    projects: list[IRProject] = field(default_factory=list)

def parse_document(entries: list[LineEntry]) -> IntermediateRepresentation:
    ir = IntermediateRepresentation()
    # Start from index 1 since the first item is the root.
    p = DocumentParser(entries)
    p.cursor = 1
    for i in range(1, len(entries)):
        prev = entries[i-1]
        match prev.type:
            case LineType.ROOT:
                e = p.consume(LineType.PROJECT)
                ir.projects.append(IRProject(e.entry))
            case LineType.PROJECT:
                match p.peek().type:
                    case LineType.TASK:
                        e = p.consume(LineType.TASK)
                        ir.projects[-1].tasks.append(IRTask(e.entry))
                    case LineType.TIME:
                        e = p.consume(LineType.TIME)
                        ir.projects[-1].tasks.append(IRTask())
                        ir.projects[-1].tasks[-1].intervals.append(IRTime(e.entry))
            case LineType.TASK:
                e = p.consume(LineType.TIME)
                ir.projects[-1].tasks[-1].intervals.append(IRTime(e.entry))
            case LineType.TIME:
                match p.peek().type:
                    case LineType.PROJECT:
                        e = p.consume(LineType.PROJECT)
                        ir.projects.append(IRProject(e.entry))
                    case LineType.TASK:
                        e = p.consume(LineType.TASK)
                        ir.projects[-1].tasks.append(IRTask(e.entry))
                    case LineType.TIME:
                        e = p.consume(LineType.TIME)
                        ir.projects[-1].tasks[-1].intervals.append(IRTime(e.entry))

    return ir

# ============================================================================
# Spreadsheet
# ============================================================================

def spreadsheet_create(ir: IntermediateRepresentation):
    wb = Workbook()
    ws = wb.active
    ws.title = "Time Tracking"

    headers = ["Date", "Project", "Task", "Start", "End", "Duration", "Hours"]
    ws.append(headers)

    ws.column_dimensions["A"].width = 15
    ws.column_dimensions["B"].width = 40
    ws.column_dimensions["C"].width = 60
    ws.column_dimensions["D"].width = 10
    ws.column_dimensions["E"].width = 10
    ws.column_dimensions["F"].width = 10
    ws.column_dimensions["G"].width = 10

    for row in spreadsheed_rows(ir):
        ws.append([
            *row,
            f"=MOD(E{ws.max_row + 1}-D{ws.max_row + 1},1)",
            f"=F{ws.max_row + 1}*24"
        ])

    for cell in ws[1]:
        cell.font = Font(bold=True)

    for row in range(2, ws.max_row + 1):
        ws[f"D{row}"].number_format = "hh:mm"
        ws[f"E{row}"].number_format = "hh:mm"
        ws[f"F{row}"].number_format = "[h]:mm"
        ws[f"G{row}"].number_format = "0.00"

    total_row = ws.max_row + 1
    ws[f"F{total_row}"] = f"=SUM(F2:F{total_row - 1})"
    ws[f"G{total_row}"] = f"=SUM(G2:G{total_row - 1})"
    ws[f"F{total_row}"].number_format = "[h]:mm"

    wb.save("time_tracking.xlsx")

def spreadsheed_rows(ir: IntermediateRepresentation) -> Iterator[list]:
    for p in ir.projects:
        for t in p.tasks:
            for i in t.intervals:
                yield [
                    p.entry.date,
                    p.entry.name,
                    t.entry.description if t.entry is not None else "",
                    i.entry.start,
                    i.entry.end,
                ]

# ============================================================================
# Utils
# ============================================================================

def date_str_to_yyyy_mm_dd(s: str) -> tuple[int, int, int]:
    date_format: str = "YYYY-MM-DD"

    if len(s) != len(date_format):
        return None

    year: str = s[:4]
    month: str = s[5:7]
    day: str = s[8:10]

    return (int(year), int(month), int(day))

def time_str_to_hh_mm(s: str) -> tuple[int, int]:
    time_format: str = "HH:mm"

    if len(s) != len(time_format):
        return None

    hour: str = s[:2]
    minute: str = s[3:]

    return (int(hour), int(minute))

# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()
