@echo off
setlocal
cd /d "%~dp0"
call "%~dp0venv\Scripts\activate.bat"
uvicorn olt_panel.main:app --host 0.0.0.0 --port 8000
