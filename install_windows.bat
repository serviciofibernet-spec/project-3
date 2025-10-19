@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Minimal Windows installer to setup venv, install deps, open firewall, and run ACS

REM Determine script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Choose Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
  echo Python not found in PATH. Please install Python 3.10+.
  pause
  exit /b 1
)

REM Create virtual environment
set VENV_DIR=.venv
if not exist "%VENV_DIR%" (
  echo Creating virtual environment in %VENV_DIR%...
  python -m venv "%VENV_DIR%"
)

REM Activate venv
call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip and install requirements
python -m pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
  echo Failed to install Python dependencies.
  pause
  exit /b 1
)

REM Open Windows Firewall port 7547 (admin privileges may be required)
where netsh >nul 2>nul
if %ERRORLEVEL% equ 0 (
  netsh advfirewall firewall add rule name="TR069_ACS_7547" dir=in action=allow protocol=TCP localport=7547 >nul 2>nul
)

REM Run the ACS server
set HOST=0.0.0.0
set PORT=7547
set THREADS=8
python -m acs_server.wsgi

pause
