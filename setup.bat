@echo off
setlocal

set /p PYTHON_VERSION=<.python-version

py -%PYTHON_VERSION% -m venv .venv

.venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo Setup complete!
pause
