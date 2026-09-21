@echo off
cd /d "%~dp0"

set "PYTHON_CMD=python"
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" 2>NUL
if errorlevel 1 (
    set "PYTHON_CMD=py -3"
    py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" 2>NUL
)
if errorlevel 1 (
    echo Python 3.12 or newer is required.
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 exit /b 1
)

venv\Scripts\python.exe -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" 2>NUL
if errorlevel 1 (
    echo Existing venv uses an older Python. Remove it and rerun this script.
    exit /b 1
)

venv\Scripts\python.exe -m pip install -e .
if errorlevel 1 exit /b 1
venv\Scripts\matrixcrypto.exe %*
