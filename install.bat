@echo off
REM ============================================================================
REM TR069 ACS Server - Windows Installer
REM ============================================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo                     TR069/CWMP ACS Server Installer
echo                              Version 1.0.0
echo ============================================================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Este instalador requiere privilegios de administrador.
    echo Por favor, ejecute como administrador.
    pause
    exit /b 1
)

REM Check Python installation
echo [1/7] Verificando instalacion de Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo.
    echo Por favor, instale Python 3.8 o superior desde:
    echo https://www.python.org/downloads/
    echo.
    echo Asegurese de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo       Python %PYTHON_VERSION% detectado.

REM Check pip installation
echo [2/7] Verificando pip...
python -m pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo       pip no encontrado. Instalando pip...
    python -m ensurepip --upgrade
    if %errorLevel% neq 0 (
        echo [ERROR] No se pudo instalar pip.
        pause
        exit /b 1
    )
)
echo       pip instalado correctamente.

REM Create installation directory
echo [3/7] Seleccionando directorio de instalacion...
set "INSTALL_DIR=%ProgramFiles%\TR069Server"
echo       Directorio: %INSTALL_DIR%

if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%" 2>nul
    if %errorLevel% neq 0 (
        echo [ERROR] No se pudo crear el directorio de instalacion.
        echo        Intentando directorio alternativo...
        set "INSTALL_DIR=%LOCALAPPDATA%\TR069Server"
        mkdir "!INSTALL_DIR!" 2>nul
        if !errorLevel! neq 0 (
            echo [ERROR] No se pudo crear el directorio de instalacion.
            pause
            exit /b 1
        )
        echo       Directorio alternativo: !INSTALL_DIR!
    )
)

REM Copy files to installation directory
echo [4/7] Copiando archivos...
xcopy /E /I /Y "tr069_server" "%INSTALL_DIR%\tr069_server" >nul 2>&1
copy /Y "main.py" "%INSTALL_DIR%\" >nul 2>&1
copy /Y "requirements.txt" "%INSTALL_DIR%\" >nul 2>&1
copy /Y "README.md" "%INSTALL_DIR%\" >nul 2>&1 2>nul
copy /Y "start_server.bat" "%INSTALL_DIR%\" >nul 2>&1
copy /Y "stop_server.bat" "%INSTALL_DIR%\" >nul 2>&1
copy /Y "uninstall.bat" "%INSTALL_DIR%\" >nul 2>&1

if %errorLevel% neq 0 (
    echo [ERROR] Error al copiar archivos.
    pause
    exit /b 1
)
echo       Archivos copiados correctamente.

REM Create necessary directories
echo [5/7] Creando directorios de datos...
mkdir "%INSTALL_DIR%\config" 2>nul
mkdir "%INSTALL_DIR%\data" 2>nul
mkdir "%INSTALL_DIR%\data\devices" 2>nul
mkdir "%INSTALL_DIR%\logs" 2>nul
echo       Directorios creados.

REM Install Python dependencies
echo [6/7] Instalando dependencias de Python...
echo       Esto puede tomar varios minutos...
cd /d "%INSTALL_DIR%"
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt >nul 2>&1
if %errorLevel% neq 0 (
    echo [ADVERTENCIA] Algunas dependencias no se pudieron instalar.
    echo              El servidor puede no funcionar correctamente.
)
echo       Dependencias instaladas.

REM Create Windows service (optional)
echo [7/7] Configurando el servicio de Windows...
choice /C SN /M "¿Desea instalar TR069 Server como servicio de Windows?"
if !errorLevel! equ 1 (
    echo       Instalando servicio...
    
    REM Create service wrapper script
    echo import sys > "%INSTALL_DIR%\service.py"
    echo import os >> "%INSTALL_DIR%\service.py"
    echo sys.path.insert(0, r'%INSTALL_DIR%') >> "%INSTALL_DIR%\service.py"
    echo os.chdir(r'%INSTALL_DIR%') >> "%INSTALL_DIR%\service.py"
    echo from main import main >> "%INSTALL_DIR%\service.py"
    echo if __name__ == '__main__': >> "%INSTALL_DIR%\service.py"
    echo     main() >> "%INSTALL_DIR%\service.py"
    
    REM Try to install pywin32 for Windows service support
    python -m pip install pywin32 >nul 2>&1
    if !errorLevel! equ 0 (
        python -m pip install pywin32-ctypes >nul 2>&1
        
        REM Create service using sc command
        sc create "TR069Server" binPath= "python.exe \"%INSTALL_DIR%\service.py\"" DisplayName= "TR069 ACS Server" start= auto >nul 2>&1
        if !errorLevel! equ 0 (
            echo       Servicio instalado correctamente.
            sc description "TR069Server" "TR069/CWMP Auto Configuration Server" >nul 2>&1
        ) else (
            echo       No se pudo crear el servicio. Puede ejecutar el servidor manualmente.
        )
    ) else (
        echo       No se pudo instalar el soporte para servicios de Windows.
        echo       Puede ejecutar el servidor manualmente con start_server.bat
    )
) else (
    echo       Servicio no instalado. Use start_server.bat para iniciar manualmente.
)

REM Create firewall rules
echo.
echo Configurando firewall de Windows...
choice /C SN /M "¿Desea crear reglas de firewall para TR069 Server?"
if !errorLevel! equ 1 (
    netsh advfirewall firewall add rule name="TR069 Server (TR069)" dir=in action=allow protocol=TCP localport=7547 >nul 2>&1
    netsh advfirewall firewall add rule name="TR069 Server (API)" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1
    echo Reglas de firewall creadas:
    echo   - Puerto 7547 (TR069/CWMP)
    echo   - Puerto 8080 (API Web)
)

REM Create desktop shortcut
echo.
choice /C SN /M "¿Desea crear accesos directos en el escritorio?"
if !errorLevel! equ 1 (
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\TR069 Server - Iniciar.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\start_server.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%SystemRoot%\System32\SHELL32.dll,13'; $Shortcut.Save()" >nul 2>&1
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\TR069 Server - Detener.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\stop_server.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%SystemRoot%\System32\SHELL32.dll,27'; $Shortcut.Save()" >nul 2>&1
    echo Accesos directos creados en el escritorio.
)

echo.
echo ============================================================================
echo                     INSTALACION COMPLETADA EXITOSAMENTE
echo ============================================================================
echo.
echo TR069 ACS Server ha sido instalado en: %INSTALL_DIR%
echo.
echo INFORMACION IMPORTANTE:
echo ------------------------
echo Servidor TR069: http://localhost:7547
echo API Web:        http://localhost:8080
echo Credenciales:   admin / admin (cambiar despues del primer inicio)
echo.
echo COMO INICIAR EL SERVIDOR:
echo ------------------------
if exist "%INSTALL_DIR%\service.py" (
    echo Opcion 1: Iniciar el servicio de Windows:
    echo           net start TR069Server
    echo.
    echo Opcion 2: Ejecutar manualmente:
    echo           %INSTALL_DIR%\start_server.bat
) else (
    echo Ejecutar: %INSTALL_DIR%\start_server.bat
    echo O usar el acceso directo en el escritorio
)
echo.
echo DOCUMENTACION:
echo ------------------------
echo Visite http://localhost:8080 despues de iniciar el servidor
echo.
echo ============================================================================
echo.

choice /C SN /M "¿Desea iniciar el servidor ahora?"
if !errorLevel! equ 1 (
    echo Iniciando TR069 Server...
    if exist "%INSTALL_DIR%\service.py" (
        net start TR069Server 2>nul
        if !errorLevel! neq 0 (
            start "" "%INSTALL_DIR%\start_server.bat"
        )
    ) else (
        start "" "%INSTALL_DIR%\start_server.bat"
    )
)

echo.
echo Presione cualquier tecla para salir...
pause >nul
exit /b 0