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

cls
echo =========================================================
echo Applying Custom DNS Settings...
echo Primary DNS:   10.11.12.13 (Private DNS Server)
echo Secondary DNS: 8.8.8.8     (Public  DNS Server)
echo =========================================================
echo.

:: Apply DNS settings to all active physical network adapters (Wi-Fi and Ethernet)

 echo applying cache speed dns
 powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' } | Set-DnsClientServerAddress -ServerAddresses ('10.11.12.13', '8.8.8.8')"

:: echo applying raw speed dns
:: powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' } | Set-DnsClientServerAddress -ServerAddresses ('8.8.8.8', '10.11.12.13')"


echo Flushing DNS Cache to apply changes immediately...
ipconfig /flushdns >nul

echo.
echo =========================================================
echo SUCCESS: Your DNS settings have been updated!
echo =========================================================
echo.
pause