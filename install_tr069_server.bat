@echo off
REM TR-069 Server Windows Installer
REM Installs Python dependencies and sets up the TR-069 server

echo ========================================
echo    TR-069 Server Installation Script
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as Administrator: OK
) else (
    echo ERROR: This script requires Administrator privileges.
    echo Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

REM Set script directory as current directory
cd /d "%~dp0"

echo Current directory: %CD%
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
) else (
    echo Python found:
    python --version
)
echo.

REM Check Python version (must be 3.8+)
echo Checking Python version compatibility...
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python 3.8 or later is required
    echo Current version:
    python --version
    pause
    exit /b 1
) else (
    echo Python version is compatible
)
echo.

REM Check if pip is available
echo Checking pip installation...
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: pip is not installed or not in PATH
    echo Please install pip or reinstall Python with pip included
    pause
    exit /b 1
) else (
    echo pip found:
    pip --version
)
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if %errorLevel% neq 0 (
    echo WARNING: Failed to upgrade pip, continuing anyway...
)
echo.

REM Install requirements
echo Installing Python dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorLevel% neq 0 (
        echo ERROR: Failed to install requirements
        pause
        exit /b 1
    )
    echo Dependencies installed successfully
) else (
    echo requirements.txt not found, installing basic dependencies...
    pip install aiohttp bcrypt PyJWT
    if %errorLevel% neq 0 (
        echo ERROR: Failed to install basic dependencies
        pause
        exit /b 1
    )
    echo Basic dependencies installed
)
echo.

REM Create configuration directory
if not exist "config" (
    echo Creating configuration directory...
    mkdir config
)

REM Create logs directory
if not exist "logs" (
    echo Creating logs directory...
    mkdir logs
)

REM Create data directory
if not exist "data" (
    echo Creating data directory...
    mkdir data
)

REM Create default configuration file
if not exist "config\server_config.json" (
    echo Creating default configuration file...
    (
        echo {
        echo   "server": {
        echo     "host": "0.0.0.0",
        echo     "port": 7547,
        echo     "ssl_enabled": false,
        echo     "ssl_cert_path": "",
        echo     "ssl_key_path": ""
        echo   },
        echo   "database": {
        echo     "devices_db": "data/tr069_devices.db",
        echo     "auth_db": "data/tr069_auth.db"
        echo   },
        echo   "logging": {
        echo     "level": "INFO",
        echo     "file": "logs/tr069_server.log",
        echo     "max_size": "10MB",
        echo     "backup_count": 5
        echo   },
        echo   "security": {
        echo     "max_failed_attempts": 5,
        echo     "block_duration_minutes": 15,
        echo     "session_timeout_hours": 24
        echo   }
        echo }
    ) > config\server_config.json
    echo Default configuration created
)

REM Create Windows service batch file
echo Creating service management scripts...
(
    echo @echo off
    echo REM Start TR-069 Server
    echo cd /d "%~dp0"
    echo call venv\Scripts\activate.bat
    echo echo Starting TR-069 Server...
    echo python tr069_server.py --config config\server_config.json
) > start_server.bat

(
    echo @echo off
    echo REM Stop TR-069 Server
    echo echo Stopping TR-069 Server...
    echo taskkill /f /im python.exe /fi "WINDOWTITLE eq TR069*"
    echo echo Server stopped
) > stop_server.bat

(
    echo @echo off
    echo REM Install TR-069 Server as Windows Service
    echo echo Installing TR-069 Server as Windows Service...
    echo echo This feature requires additional setup.
    echo echo Please refer to the documentation for service installation.
    echo pause
) > install_service.bat

echo Service management scripts created
echo.

REM Create desktop shortcut (optional)
set /p create_shortcut="Create desktop shortcut? (y/n): "
if /i "%create_shortcut%"=="y" (
    echo Creating desktop shortcut...
    powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\TR-069 Server.lnk'); $Shortcut.TargetPath = '%CD%\start_server.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.IconLocation = 'shell32.dll,21'; $Shortcut.Save()"
    if %errorLevel% == 0 (
        echo Desktop shortcut created
    ) else (
        echo Failed to create desktop shortcut
    )
)
echo.

REM Create firewall rule (optional)
set /p create_firewall="Create Windows Firewall rule for port 7547? (y/n): "
if /i "%create_firewall%"=="y" (
    echo Creating Windows Firewall rule...
    netsh advfirewall firewall add rule name="TR-069 Server" dir=in action=allow protocol=TCP localport=7547
    if %errorLevel% == 0 (
        echo Firewall rule created successfully
    ) else (
        echo Failed to create firewall rule - you may need to configure it manually
    )
)
echo.

REM Test installation
echo Testing installation...
python -c "import aiohttp, bcrypt; print('All required modules are available')"
if %errorLevel% neq 0 (
    echo ERROR: Installation test failed
    pause
    exit /b 1
)
echo Installation test passed
echo.

REM Display installation summary
echo ========================================
echo        Installation Complete!
echo ========================================
echo.
echo Installation directory: %CD%
echo Virtual environment: %CD%\venv
echo Configuration file: %CD%\config\server_config.json
echo.
echo To start the server:
echo   1. Double-click start_server.bat, or
echo   2. Run: python tr069_server.py
echo.
echo To stop the server:
echo   1. Double-click stop_server.bat, or
echo   2. Press Ctrl+C in the server window
echo.
echo Server will be accessible at:
echo   HTTP: http://localhost:7547
echo   Status: http://localhost:7547/status
echo   Devices: http://localhost:7547/devices
echo.
echo Default admin credentials:
echo   Username: admin
echo   Password: admin123
echo   ^(CHANGE THIS IMMEDIATELY!^)
echo.
echo Configuration file location:
echo   %CD%\config\server_config.json
echo.
echo Log files location:
echo   %CD%\logs\
echo.
echo For more information, see README.md
echo.

REM Ask if user wants to start the server now
set /p start_now="Start the TR-069 server now? (y/n): "
if /i "%start_now%"=="y" (
    echo.
    echo Starting TR-069 server...
    echo Press Ctrl+C to stop the server
    echo.
    python tr069_server.py
) else (
    echo.
    echo Installation complete. You can start the server later using start_server.bat
)

echo.
echo Press any key to exit...
pause >nul