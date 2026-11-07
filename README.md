# Markdown Time Tracking Exporter

Converts a Markdown file using a simple time-tracking syntax into an Excel spreadsheet.

The generated spreadsheet is fully inspectable, with formulas to calculate time intervals and total hours automatically.

## Syntax

```markdown
- [ ] 2026-01-01: [[Feature - PR 1]]
    - 09:00-10:00
    - 12:00-13:00 # Comment: Second time entry
- [ ] 2026-01-02: [[Feature - PR 2]]
    - Task description # Nested task entry
        - 20:15-22:00
```

## Usage

By default, the script uses the Markdown file at `test/time_tracking.md`.
To provide custom Markdown content, you can pass it directly through the command line:

```bat
py main.py --text "markdown_content"
```

## Python

This project uses Python and a virtual environment (`venv`).

### Windows

Run the following command from Command Prompt to set up the project:

```bat
setup.bat
```

It automatically reads the required Python version from `.python-version`, creates the virtual environment, and installs the dependencies listed in `requirements.txt`.

To activate the virtual environment:

```bat
.venv\Scripts\activate.bat
```
