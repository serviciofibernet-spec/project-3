@echo off
setlocal enabledelayedexpansion

REM ==========================
REM  Instalador OLT C300 V2
REM ==========================

REM Cambiar al directorio del script
cd /d "%~dp0"

echo === Instalador Panel OLT C300 V2 ===

REM Detectar Python 3.10/3.x
set "PYTHON_CMD="
where py >nul 2>nul && (
  py -3.10 -V >nul 2>nul && set "PYTHON_CMD=py -3.10"
  if not defined PYTHON_CMD (
    py -3 -V >nul 2>nul && set "PYTHON_CMD=py -3"
  )
)
if not defined PYTHON_CMD (
  where python >nul 2>nul && set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
  echo [ERROR] No se encontro Python 3.x en PATH.
  echo Instale Python 3.10+ y marque "Add Python to PATH".
  pause
  exit /b 1
)

REM Crear venv si no existe
if not exist "venv" (
  echo Creando entorno virtual...
  %PYTHON_CMD% -m venv "venv"
  if errorlevel 1 (
    echo [ERROR] Fallo creando el entorno virtual.
    pause
    exit /b 1
  )
)

REM Activar venv
call "%~dp0venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] No se pudo activar el entorno virtual.
  pause
  exit /b 1
)

echo Actualizando pip...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] Fallo al actualizar pip.
  pause
  exit /b 1
)

echo Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Fallo al instalar dependencias. Revise su conexion a Internet.
  pause
  exit /b 1
)

REM Crear config por defecto si no existe
if exist "config.example.yml" (
  if not exist "config.yml" (
    copy /Y "config.example.yml" "config.yml" >nul
    echo Se creo config.yml a partir de config.example.yml
  )
)

echo.
echo Instalacion completada.
echo Use run.bat para iniciar el servidor.
echo El panel estara en http://localhost:8000/
pause
exit /b 0
