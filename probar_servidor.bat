@echo off
REM Script para probar la conexión al servidor TR-069

title Test Conexión TR-069 Server

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║     Test de Conexión - TR-069 ACS Server            ║
echo ╚══════════════════════════════════════════════════════╝
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado
    echo.
    pause
    exit /b 1
)

echo Ejecutando tests de conexión...
echo.

python test_conexion.py

pause
