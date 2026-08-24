@echo off
SETLOCAL
SET SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo Installation complete. Run run.bat to start the application.
ENDLOCAL
