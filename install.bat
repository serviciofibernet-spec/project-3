@echo off
setlocal enabledelayedexpansion

REM Change to script directory
cd /d "%~dp0"

REM Create venv if missing
if not exist "venv" (
  echo Creating virtual environment...
  where py >nul 2>nul && (py -3 -m venv venv) || (python -m venv venv)
)

REM Activate venv and install dependencies
call "%~dp0venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Seed a default config if none exists
if exist "config.example.yml" (
  if not exist "config.yml" copy /Y "config.example.yml" "config.yml" >nul
)

echo.
echo Installation complete.
echo Use run.bat to start the server.
echo The panel will be at http://localhost:8000/
exit /b 0
