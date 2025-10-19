@echo off
REM ================================================================
REM Instalador TR-069 ACS Server para Windows
REM ================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     Instalador TR-069 ACS Server v1.0 para Windows          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Verificar si Python está instalado
echo [1/5] Verificando instalación de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo.
    echo Por favor, instala Python 3.7 o superior desde:
    echo https://www.python.org/downloads/
    echo.
    echo Asegúrate de marcar "Add Python to PATH" durante la instalación
    echo.
    pause
    exit /b 1
)

python --version
echo ✓ Python encontrado
echo.

REM Verificar versión de Python
echo [2/5] Verificando versión de Python...
python -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Se requiere Python 3.7 o superior
    echo.
    pause
    exit /b 1
)
echo ✓ Versión de Python correcta
echo.

REM Crear directorio de instalación si no existe
echo [3/5] Preparando directorios...
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo ✓ Directorios preparados
echo.

REM Instalar dependencias (opcional, ya que no hay externas requeridas)
echo [4/5] Verificando dependencias...
if exist requirements.txt (
    echo Instalando dependencias desde requirements.txt...
    python -m pip install --upgrade pip >nul 2>&1
    python -m pip install -r requirements.txt >nul 2>&1
    if errorlevel 1 (
        echo ⚠ Advertencia: Algunas dependencias opcionales no se pudieron instalar
        echo El servidor funcionará con las bibliotecas estándar de Python
    ) else (
        echo ✓ Dependencias instaladas
    )
) else (
    echo ℹ No se encontró requirements.txt, usando bibliotecas estándar
)
echo.

REM Verificar archivos necesarios
echo [5/5] Verificando archivos del servidor...
if not exist tr069_server.py (
    echo ❌ ERROR: No se encuentra tr069_server.py
    pause
    exit /b 1
)
echo ✓ Archivo del servidor encontrado
echo.

REM Crear configuración por defecto si no existe
if not exist tr069_config.json (
    echo Creando configuración por defecto...
    echo ℹ Puedes editar tr069_config.json para personalizar la configuración
)
echo.

REM Crear script de inicio rápido
echo [EXTRA] Creando accesos directos...
(
echo @echo off
echo title TR-069 ACS Server
echo python tr069_server.py
echo pause
) > iniciar_servidor.bat
echo ✓ Archivo 'iniciar_servidor.bat' creado
echo.

REM Crear script de parada
(
echo @echo off
echo title Detener TR-069 Server
echo echo Buscando proceso del servidor...
echo for /f "tokens=2" %%%%i in ^('tasklist ^| findstr /i python'^ do ^(
echo     echo Proceso Python encontrado: %%%%i
echo ^)
echo echo.
echo echo Presiona Ctrl+C en la ventana del servidor para detenerlo
echo pause
) > detener_servidor.bat
echo ✓ Archivo 'detener_servidor.bat' creado
echo.

echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  ✓ INSTALACIÓN COMPLETADA                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 📋 Configuración:
echo    - Puerto: 7547 (por defecto)
echo    - Usuario: admin
echo    - Contraseña: admin123
echo.
echo 🚀 Para iniciar el servidor:
echo    1. Ejecuta: iniciar_servidor.bat
echo    2. O ejecuta: python tr069_server.py
echo.
echo 🌐 Panel de control:
echo    http://localhost:7547/
echo.
echo 📝 Archivos importantes:
echo    - tr069_server.py        : Servidor principal
echo    - tr069_config.json      : Configuración
echo    - tr069_devices.json     : Base de datos de dispositivos
echo    - tr069_server.log       : Registro de eventos
echo    - iniciar_servidor.bat   : Inicio rápido
echo.
echo 📖 Para más información, consulta README.md
echo.
pause
