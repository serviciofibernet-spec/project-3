@echo off
REM ============================================================================
REM TR069 ACS Server - Stop Script
REM ============================================================================
setlocal

echo.
echo ============================================================================
echo                        Deteniendo TR069 ACS Server
echo ============================================================================
echo.

REM First try to stop the Windows service if it exists
echo Verificando servicio de Windows...
sc query "TR069Server" >nul 2>&1
if %errorLevel% equ 0 (
    echo Deteniendo servicio TR069Server...
    net stop "TR069Server"
    if %errorLevel% equ 0 (
        echo Servicio detenido exitosamente.
    ) else (
        echo No se pudo detener el servicio o ya estaba detenido.
    )
) else (
    echo Servicio de Windows no encontrado.
)

REM Kill Python processes running main.py
echo.
echo Buscando procesos del servidor...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fi "windowtitle eq *TR069*" /fo list 2^>nul ^| find "PID:"') do (
    echo Deteniendo proceso con PID %%i...
    taskkill /PID %%i /F >nul 2>&1
)

REM Also try to kill processes by command line
wmic process where "name='python.exe' and commandline like '%%main.py%%'" delete >nul 2>&1

echo.
echo ============================================================================
echo                              SERVIDOR DETENIDO
echo ============================================================================
echo.
echo El servidor TR069 ACS ha sido detenido.
echo.
echo Para reiniciar el servidor, ejecute start_server.bat
echo ============================================================================
echo.

pause
exit /b 0