@echo off
REM ============================================================================
REM TR069 ACS Server - Configuration Tool
REM ============================================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo                   TR069 ACS Server - Herramienta de Configuracion
echo ============================================================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    pause
    exit /b 1
)

REM Create config directory if not exists
if not exist "config" mkdir "config"

echo Este asistente le ayudara a configurar el servidor TR069.
echo.

REM Server configuration
echo === CONFIGURACION DEL SERVIDOR ===
echo.

set /p TR069_HOST="Direccion IP del servidor TR069 [0.0.0.0]: "
if "!TR069_HOST!"=="" set TR069_HOST=0.0.0.0

set /p TR069_PORT="Puerto del servidor TR069 [7547]: "
if "!TR069_PORT!"=="" set TR069_PORT=7547

set /p API_HOST="Direccion IP de la API [0.0.0.0]: "
if "!API_HOST!"=="" set API_HOST=0.0.0.0

set /p API_PORT="Puerto de la API [8080]: "
if "!API_PORT!"=="" set API_PORT=8080

echo.
echo === CONFIGURACION DE SEGURIDAD ===
echo.

set /p ADMIN_USER="Usuario administrador [admin]: "
if "!ADMIN_USER!"=="" set ADMIN_USER=admin

set /p ADMIN_PASS="Contraseña administrador [admin]: "
if "!ADMIN_PASS!"=="" set ADMIN_PASS=admin

echo.
echo === CONFIGURACION DE LOGS ===
echo.

echo Nivel de log:
echo   1. DEBUG (muy detallado)
echo   2. INFO (normal)
echo   3. WARNING (solo advertencias y errores)
echo   4. ERROR (solo errores)
echo.
choice /C 1234 /N /M "Seleccione nivel de log [2]: " /D 2 /T 5
if !errorLevel! equ 1 set LOG_LEVEL=DEBUG
if !errorLevel! equ 2 set LOG_LEVEL=INFO
if !errorLevel! equ 3 set LOG_LEVEL=WARNING
if !errorLevel! equ 4 set LOG_LEVEL=ERROR

REM Create server configuration
echo.
echo Creando archivo de configuracion...

(
echo {
echo   "host": "!TR069_HOST!",
echo   "port": !TR069_PORT!,
echo   "api_host": "!API_HOST!",
echo   "api_port": !API_PORT!,
echo   "log_level": "!LOG_LEVEL!",
echo   "description": "TR069/CWMP ACS Server Configuration",
echo   "session_timeout": 3600,
echo   "max_devices": 1000,
echo   "enable_auth": true,
echo   "enable_ssl": false,
echo   "ssl_cert": "",
echo   "ssl_key": ""
echo }
) > config\server.json

echo Configuracion guardada en config\server.json

REM Create Python configuration script for admin user
echo.
echo Configurando usuario administrador...

(
echo import sys
echo import os
echo sys.path.insert(0, os.path.dirname(os.path.abspath(__file__^)^)^)
echo from tr069_server.auth import AuthManager
echo.
echo auth = AuthManager(^)
echo auth.create_user("!ADMIN_USER!", "!ADMIN_PASS!", "Administrator", ["admin"]^)
echo print("Usuario administrador configurado correctamente."^)
) > temp_config.py

python temp_config.py
del temp_config.py

echo.
echo === CONFIGURACION DE DISPOSITIVOS ===
echo.

choice /C SN /M "¿Desea configurar autenticacion para dispositivos CPE?"
if !errorLevel! equ 1 (
    echo.
    echo Ingrese las credenciales por defecto para dispositivos:
    set /p CPE_USER="Usuario CPE [cpe]: "
    if "!CPE_USER!"=="" set CPE_USER=cpe
    
    set /p CPE_PASS="Contraseña CPE [cpe123]: "
    if "!CPE_PASS!"=="" set CPE_PASS=cpe123
    
    (
    echo {
    echo   "default_username": "!CPE_USER!",
    echo   "default_password": "!CPE_PASS!",
    echo   "auto_register": true,
    echo   "require_auth": true
    echo }
    ) > config\cpe_auth.json
    
    echo Configuracion de dispositivos guardada.
) else (
    (
    echo {
    echo   "auto_register": true,
    echo   "require_auth": false
    echo }
    ) > config\cpe_auth.json
)

echo.
echo === RESUMEN DE CONFIGURACION ===
echo.
echo Servidor TR069:    http://!TR069_HOST!:!TR069_PORT!
echo API Web:           http://!API_HOST!:!API_PORT!
echo Usuario Admin:     !ADMIN_USER!
echo Nivel de Log:      !LOG_LEVEL!
echo.

choice /C SN /M "¿Desea crear un archivo de configuracion de ejemplo para dispositivos CPE?"
if !errorLevel! equ 1 (
    echo.
    echo Creando archivo de ejemplo para CPE...
    
    REM Get local IP
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4"') do (
        for /f "tokens=1" %%b in ("%%a") do (
            set LOCAL_IP=%%b
        )
    )
    
    (
    echo # Configuracion CPE para TR069 Server
    echo # =====================================
    echo.
    echo ACS URL: http://!LOCAL_IP!:!TR069_PORT!/
    echo ACS Username: !CPE_USER!
    echo ACS Password: !CPE_PASS!
    echo.
    echo Periodic Inform Enable: 1
    echo Periodic Inform Interval: 3600
    echo.
    echo Connection Request Username: admin
    echo Connection Request Password: admin
    echo.
    echo # Para routers TP-Link:
    echo # System Tools -^> TR-069 Client -^> ACS Server
    echo.
    echo # Para routers Huawei:
    echo # WAN -^> TR069 Config -^> ACS URL
    echo.
    echo # Para routers ZTE:
    echo # Administration -^> TR069 -^> ACS Settings
    ) > CPE_CONFIG_EXAMPLE.txt
    
    echo Archivo creado: CPE_CONFIG_EXAMPLE.txt
)

echo.
echo ============================================================================
echo                      CONFIGURACION COMPLETADA
echo ============================================================================
echo.
echo La configuracion ha sido guardada exitosamente.
echo.
echo Para aplicar los cambios, reinicie el servidor:
echo   1. Ejecute stop_server.bat
echo   2. Ejecute start_server.bat
echo.
echo ============================================================================
echo.

pause
exit /b 0