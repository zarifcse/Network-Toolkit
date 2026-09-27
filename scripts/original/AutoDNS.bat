@echo off
title Reset DNS to Automatic
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cls
echo Resetting DNS to Automatic (DHCP)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' } | Set-DnsClientServerAddress -ResetServerAddresses"
ipconfig /flushdns >nul

echo.
echo SUCCESS: DNS has been reset to Automatic!
echo.
pause