@echo off
setlocal
cd /d "%~dp0"

echo === Panel OLT C300 V2 ===

if not exist "venv\Scripts\activate.bat" (
  echo No se encontro el entorno virtual. Ejecutando instalador...
  call "%~dp0install.bat"
)

call "%~dp0venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] No se pudo activar el entorno virtual.
  pause
  exit /b 1
)

echo Iniciando servidor en http://localhost:8000 ...
uvicorn olt_panel.main:app --host 0.0.0.0 --port 8000
if errorlevel 1 (
  echo [ERROR] Error al iniciar el servidor.
  pause
  exit /b 1
)

echo Servidor detenido. Presione una tecla para cerrar.
pause
exit /b 0
