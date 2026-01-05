@echo off
REM Quick setup script for 3proxy on Windows
REM Run as Administrator

echo ==========================================
echo   Home Proxy Setup for Terabox Bot
echo ==========================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please run as Administrator
    echo Right-click this file and select "Run as Administrator"
    pause
    exit /b 1
)

REM Configuration
set /p PROXY_USER="Enter proxy username [terabox]: "
if "%PROXY_USER%"=="" set PROXY_USER=terabox

set /p PROXY_PASS="Enter proxy password: "
if "%PROXY_PASS%"=="" (
    echo ERROR: Password cannot be empty
    pause
    exit /b 1
)

set /p SOCKS_PORT="Enter SOCKS5 port [1080]: "
if "%SOCKS_PORT%"=="" set SOCKS_PORT=1080

set /p HTTP_PORT="Enter HTTP proxy port [3128]: "
if "%HTTP_PORT%"=="" set HTTP_PORT=3128

echo.
echo Configuration:
echo    Username: %PROXY_USER%
echo    Password: ********
echo    SOCKS5 Port: %SOCKS_PORT%
echo    HTTP Port: %HTTP_PORT%
echo.

set /p CONFIRM="Continue with installation? (Y/N): "
if /i not "%CONFIRM%"=="Y" exit /b 0

REM Create installation directory
set INSTALL_DIR=C:\3proxy
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo.
echo Downloading 3proxy...
echo Please download 3proxy manually from:
echo https://github.com/3proxy/3proxy/releases
echo.
echo Download: 3proxy-0.9.4.x86_64.zip (or latest version)
echo Extract to: %INSTALL_DIR%
echo.
pause

REM Check if 3proxy.exe exists
if not exist "%INSTALL_DIR%\3proxy.exe" (
    echo ERROR: 3proxy.exe not found in %INSTALL_DIR%
    echo Please download and extract 3proxy first
    pause
    exit /b 1
)

REM Create configuration file
echo.
echo Creating configuration...
(
echo # 3proxy configuration for Terabox Bot
echo nserver 8.8.8.8
echo nserver 8.8.4.4
echo.
echo # Log settings
echo log "%INSTALL_DIR%\3proxy.log" D
echo logformat "- +_L%%t.%%. %%N.%%p %%E %%U %%C:%%c %%R:%%r %%O %%I %%h %%T"
echo rotate 30
echo.
echo # Authentication
echo users %PROXY_USER%:CL:%PROXY_PASS%
echo.
echo # SOCKS5 proxy
echo auth strong
echo allow %PROXY_USER%
echo socks -p%SOCKS_PORT%
echo.
echo # HTTP proxy
echo auth strong
echo allow %PROXY_USER%
echo proxy -p%HTTP_PORT%
) > "%INSTALL_DIR%\3proxy.cfg"

REM Create start script
echo.
echo Creating start script...
(
echo @echo off
echo cd /d "%INSTALL_DIR%"
echo 3proxy.exe 3proxy.cfg
) > "%INSTALL_DIR%\start.bat"

REM Create service installer script
echo.
echo Creating service installer...
(
echo @echo off
echo REM Install 3proxy as Windows Service
echo sc create 3proxy binPath= "\"%INSTALL_DIR%\3proxy.exe\" \"%INSTALL_DIR%\3proxy.cfg\"" start= auto
echo sc description 3proxy "3proxy Proxy Server for Terabox Bot"
echo sc start 3proxy
echo echo Service installed and started
echo pause
) > "%INSTALL_DIR%\install_service.bat"

REM Configure Windows Firewall
echo.
echo Configuring Windows Firewall...
netsh advfirewall firewall add rule name="3proxy SOCKS5" dir=in action=allow protocol=TCP localport=%SOCKS_PORT%
netsh advfirewall firewall add rule name="3proxy HTTP" dir=in action=allow protocol=TCP localport=%HTTP_PORT%

REM Get local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP:~1%

echo.
echo ==========================================
echo   Setup Complete!
echo ==========================================
echo.
echo Installation Directory: %INSTALL_DIR%
echo Config File: %INSTALL_DIR%\3proxy.cfg
echo Log File: %INSTALL_DIR%\3proxy.log
echo.
echo Your Local IP: %LOCAL_IP%
echo.
echo Next Steps:
echo.
echo 1. Start 3proxy:
echo    Option A: Run %INSTALL_DIR%\start.bat as Administrator
echo    Option B: Install as service (recommended):
echo              Run %INSTALL_DIR%\install_service.bat as Administrator
echo.
echo 2. Test locally:
echo    curl --socks5 localhost:%SOCKS_PORT% --proxy-user %PROXY_USER%:%PROXY_PASS% https://api.ipify.org
echo.
echo 3. Configure port forwarding on your router:
echo    - Forward port %SOCKS_PORT% to %LOCAL_IP%:%SOCKS_PORT% (TCP)
echo    - Forward port %HTTP_PORT% to %LOCAL_IP%:%HTTP_PORT% (TCP)
echo.
echo 4. Set up Dynamic DNS (if no static IP):
echo    - Sign up at https://www.noip.com/ or https://www.duckdns.org/
echo    - Create hostname (e.g., yourname.ddns.net)
echo.
echo 5. Add to Railway environment variables:
echo    PROXY_URL=socks5://%PROXY_USER%:%PROXY_PASS%@yourname.ddns.net:%SOCKS_PORT%
echo.
echo 6. Test from external network:
echo    curl --socks5 yourname.ddns.net:%SOCKS_PORT% --proxy-user %PROXY_USER%:%PROXY_PASS% https://api.ipify.org
echo.
echo Full guide: HOME_PROXY_SETUP.md
echo ==========================================
echo.
pause
