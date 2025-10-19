@echo off
echo ========================================
echo    TR-069 Server Installer for Windows
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found! Checking version...
python --version

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not available
    echo Please reinstall Python with pip included
    pause
    exit /b 1
)

echo.
echo Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Creating startup script...
echo @echo off > start_tr069_server.bat
echo echo Starting TR-069 Server... >> start_tr069_server.bat
echo echo Server will be available at: >> start_tr069_server.bat
echo echo   - HTTP: http://localhost:8080 >> start_tr069_server.bat
echo echo   - Web Interface: http://localhost:8080/ >> start_tr069_server.bat
echo echo   - TR-069 Endpoint: http://localhost:8080/tr069 >> start_tr069_server.bat
echo echo. >> start_tr069_server.bat
echo echo Press Ctrl+C to stop the server >> start_tr069_server.bat
echo echo. >> start_tr069_server.bat
echo python tr069_server.py >> start_tr069_server.bat

echo.
echo Creating configuration file...
echo # TR-069 Server Configuration > config.ini
echo [server] >> config.ini
echo host = 0.0.0.0 >> config.ini
echo port = 8080 >> config.ini
echo ssl_port = 8443 >> config.ini
echo >> config.ini
echo [logging] >> config.ini
echo level = INFO >> config.ini
echo file = tr069_server.log >> config.ini

echo.
echo Creating firewall rule (requires administrator privileges)...
netsh advfirewall firewall add rule name="TR-069 Server" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1
if %errorlevel% equ 0 (
    echo Firewall rule added successfully
) else (
    echo Warning: Could not add firewall rule. You may need to run as administrator
)

echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo To start the TR-069 server:
echo   1. Double-click 'start_tr069_server.bat'
echo   2. Or run: python tr069_server.py
echo.
echo Server endpoints:
echo   - Web Interface: http://localhost:8080/
echo   - TR-069 SOAP: http://localhost:8080/tr069
echo   - REST API: http://localhost:8080/devices
echo.
echo Logs will be saved to: tr069_server.log
echo.
echo Press any key to exit...
pause >nul