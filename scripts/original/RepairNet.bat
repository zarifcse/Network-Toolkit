@echo off
:: Automatically check and request Administrator privileges safely
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :RunCommands
) else (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:RunCommands
:: Force Windows to keep the script in its actual folder location
cd /d "%~dp0"
title Deep Network Repair and Reset Tool
cls

echo ===================================================
echo           STARTING DEEP NETWORK REPAIR          
echo ===================================================
echo.

echo [1/7] Releasing current IP configurations...
ipconfig /release
echo.

echo [2/7] Flushing DNS Resolver Cache...
ipconfig /flushdns
echo.

echo [3/7] Clearing Local ARP Hardware Cache...
arp -d *
echo.

echo [4/7] Resetting NetBIOS Name Cache...
nbtstat -R
nbtstat -RR
echo.

echo [5/7] Resetting Winsock Catalog (Deep Registry Clean)...
netsh winsock reset
echo.

echo [6/7] Resetting TCP/IP Stack...
echo (Note: If Windows says "Access is denied" on a line below, ignore it. It is harmless!)
netsh int ip reset
echo.

echo [7/7] Renewing IP address with the Router...
ipconfig /renew
echo.

echo ===================================================
echo   Deep repair complete! Closing in 10 seconds.
echo ===================================================
echo Note: Windows recommends a restart for 100% effect,
echo but if your internet works now, no restart is needed!
echo.
timeout /t 10
exit