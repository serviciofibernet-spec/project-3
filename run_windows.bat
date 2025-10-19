@echo off
setlocal enabledelayedexpansion

REM Ensure we run from the script directory
cd /d "%~dp0"

set "VENV_DIR=.venv"

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment in %VENV_DIR%...
    py -3 -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Falling back to 'py -m venv'...
        py -m venv "%VENV_DIR%"
        if errorlevel 1 (
            echo Falling back to 'python -m venv'...
            python -m venv "%VENV_DIR%"
            if errorlevel 1 (
                echo Failed to create virtual environment. Ensure Python 3 is installed and on PATH.
                exit /b 1
            )
        )
    )
)

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    exit /b 1
)

set "PORT=7547"
if exist .env (
  for /f "tokens=1,* delims==" %%A in ('type .env ^| findstr /i ^PORT=') do (
    set "PORT=%%B"
  )
)

echo Starting TR-069 ACS on http://127.0.0.1:%PORT% ...
uvicorn main:app --host 0.0.0.0 --port %PORT%
