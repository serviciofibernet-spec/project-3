@echo off
REM ============================================================================
REM TR069 ACS Server - Uninstaller
REM ============================================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo                     TR069/CWMP ACS Server - Desinstalador
echo ============================================================================
echo.
echo ADVERTENCIA: Este proceso eliminara completamente TR069 Server de su sistema.
echo              Todos los datos y configuraciones seran eliminados.
echo.

choice /C SN /M "¿Esta seguro que desea desinstalar TR069 Server?"
if !errorLevel! neq 1 (
    echo.
    echo Desinstalacion cancelada.
    pause
    exit /b 0
)

echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Este desinstalador requiere privilegios de administrador.
    echo Por favor, ejecute como administrador.
    pause
    exit /b 1
)

REM Get installation directory
set "INSTALL_DIR=%~dp0"
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo [1/6] Deteniendo servicios...

REM Stop and remove Windows service
sc query "TR069Server" >nul 2>&1
if %errorLevel% equ 0 (
    echo       Deteniendo servicio de Windows...
    net stop "TR069Server" >nul 2>&1
    timeout /t 2 >nul
    
    echo       Eliminando servicio de Windows...
    sc delete "TR069Server" >nul 2>&1
    if %errorLevel% equ 0 (
        echo       Servicio eliminado.
    )
) else (
    echo       No se encontro servicio de Windows.
)

REM Kill any running Python processes
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fi "windowtitle eq *TR069*" /fo list 2^>nul ^| find "PID:"') do (
    taskkill /PID %%i /F >nul 2>&1
)
wmic process where "name='python.exe' and commandline like '%%main.py%%'" delete >nul 2>&1

echo [2/6] Eliminando reglas de firewall...
netsh advfirewall firewall delete rule name="TR069 Server (TR069)" >nul 2>&1
netsh advfirewall firewall delete rule name="TR069 Server (API)" >nul 2>&1
echo       Reglas de firewall eliminadas.

echo [3/6] Eliminando accesos directos...
del "%USERPROFILE%\Desktop\TR069 Server - Iniciar.lnk" >nul 2>&1
del "%USERPROFILE%\Desktop\TR069 Server - Detener.lnk" >nul 2>&1
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\TR069 Server - Iniciar.lnk" >nul 2>&1
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\TR069 Server - Detener.lnk" >nul 2>&1
echo       Accesos directos eliminados.

echo [4/6] Respaldando datos...
choice /C SN /M "¿Desea hacer una copia de seguridad de los datos antes de eliminar?"
if !errorLevel! equ 1 (
    set "BACKUP_DIR=%USERPROFILE%\Documents\TR069Server_Backup_%DATE:~6,4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%"
    set "BACKUP_DIR=!BACKUP_DIR: =0!"
    mkdir "!BACKUP_DIR!" >nul 2>&1
    
    if exist "%INSTALL_DIR%\config" (
        xcopy /E /I /Y "%INSTALL_DIR%\config" "!BACKUP_DIR!\config" >nul 2>&1
    )
    if exist "%INSTALL_DIR%\data" (
        xcopy /E /I /Y "%INSTALL_DIR%\data" "!BACKUP_DIR!\data" >nul 2>&1
    )
    if exist "%INSTALL_DIR%\logs" (
        xcopy /E /I /Y "%INSTALL_DIR%\logs" "!BACKUP_DIR!\logs" >nul 2>&1
    )
    
    echo       Respaldo creado en: !BACKUP_DIR!
) else (
    echo       Respaldo omitido.
)

echo [5/6] Eliminando archivos de instalacion...
echo       Eliminando: %INSTALL_DIR%

REM Create a temporary batch file to delete the installation directory
set "TEMP_BAT=%TEMP%\tr069_cleanup.bat"
echo @echo off > "%TEMP_BAT%"
echo timeout /t 3 ^>nul >> "%TEMP_BAT%"
echo rd /s /q "%INSTALL_DIR%" >> "%TEMP_BAT%"
echo del "%%~f0" >> "%TEMP_BAT%"

echo       Archivos programados para eliminacion.

echo [6/6] Limpieza final...
echo       Desinstalacion casi completa.

echo.
echo ============================================================================
echo                      DESINSTALACION COMPLETADA
echo ============================================================================
echo.
if defined BACKUP_DIR (
    echo Sus datos han sido respaldados en:
    echo   !BACKUP_DIR!
    echo.
)
echo TR069 ACS Server ha sido desinstalado de su sistema.
echo.
echo El directorio de instalacion sera eliminado cuando cierre esta ventana.
echo ============================================================================
echo.
echo Presione cualquier tecla para finalizar...
pause >nul

REM Execute cleanup batch
start /b "" cmd /c "%TEMP_BAT%"
exit