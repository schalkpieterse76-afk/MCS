@echo off
SETLOCAL
SET SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"
call venv\Scripts\activate.bat
python mcs_cvor\main.py
ENDLOCAL
