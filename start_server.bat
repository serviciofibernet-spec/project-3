@echo off
REM ============================================================================
REM TR069 ACS Server - Start Script
REM ============================================================================
setlocal

echo.
echo ============================================================================
echo                        Iniciando TR069 ACS Server
echo ============================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    pause
    exit /b 1
)

REM Get current directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if main.py exists
if not exist "main.py" (
    echo [ERROR] No se encuentra main.py en el directorio actual.
    echo         Asegurese de ejecutar este script desde el directorio de instalacion.
    pause
    exit /b 1
)

REM Create necessary directories if they don't exist
if not exist "config" mkdir "config"
if not exist "data" mkdir "data"
if not exist "data\devices" mkdir "data\devices"
if not exist "logs" mkdir "logs"

echo Verificando dependencias...
python -c "import flask" 2>nul
if %errorLevel% neq 0 (
    echo Instalando dependencias faltantes...
    python -m pip install -r requirements.txt
)

echo.
echo ============================================================================
echo                            SERVIDOR INICIANDO
echo ============================================================================
echo.
echo Servidor TR069/CWMP: http://localhost:7547
echo API de Administracion: http://localhost:8080
echo.
echo Credenciales por defecto:
echo   Usuario: admin
echo   Contraseña: admin
echo.
echo Para detener el servidor, presione Ctrl+C o cierre esta ventana.
echo ============================================================================
echo.

REM Start the server
python main.py

if %errorLevel% neq 0 (
    echo.
    echo [ERROR] El servidor se detuvo con errores.
    echo         Revise los logs en el directorio 'logs' para mas informacion.
    pause
)

exit /b %errorLevel%