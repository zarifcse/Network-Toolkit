@echo off
title Custom DNS Configurator
color 0A

:: Check and request Administrator privileges automatically
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:MENU
cls
echo =========================================================
echo                 DNS CONFIGURATION MENU
echo =========================================================
echo [1] Apply Cache Speed DNS (Epic/Steam Cache: 10.11.12.13)
echo [2] Apply Raw Speed DNS   (Direct Gaming/Web: 1.1.1.1)
echo [3] Exit
echo =========================================================
echo.

:: Prompts the user to select one item from the choices
choice /C 123 /N /M "Press a number key [1, 2, or 3] to choose an option: "

:: When you use ERRORLEVEL values in a batch program, you must list them in decreasing order
if errorlevel 3 goto EXIT
if errorlevel 2 goto RAW_SPEED
if errorlevel 1 goto CACHE_SPEED

:CACHE_SPEED
cls
echo =========================================================
echo Applying Cache Speed DNS (10.11.12.13, 8.8.8.8)...
echo =========================================================
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' } | Set-DnsClientServerAddress -ServerAddresses ('10.11.12.13', '8.8.8.8')"
goto FLUSH

:RAW_SPEED
cls
echo =========================================================
echo Applying Raw Speed DNS (8.8.8.8, 1.1.1.1)...
echo =========================================================
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' } | Set-DnsClientServerAddress -ServerAddresses ('8.8.8.8', '1.1.1.1')"
goto FLUSH

:FLUSH
echo.
echo Flushing DNS Cache to apply changes immediately...
ipconfig /flushdns >nul
echo.
echo =========================================================
echo SUCCESS: Your DNS settings have been updated!
echo =========================================================
echo.
pause
goto MENU

:EXIT
exit