@echo off
:: ---------------------------------------------------------
:: QUICK NETWORK REFRESH TOOL
:: No Administrator privileges required.
:: ---------------------------------------------------------

:: Set terminal color (0B = Light Aqua text on Black background)
color 0B

:: Force Windows to keep the script in its actual folder location
cd /d "%~dp0"
title Quick Network Refresh Tool
cls

echo ==========================================================
echo                QUICK NETWORK REFRESH TOOL                 
echo ==========================================================
echo.

echo [1/3] Releasing current IP address...
echo ----------------------------------------------------------
ipconfig /release
echo.

echo [2/3] Clearing DNS Cache...
echo ----------------------------------------------------------
ipconfig /flushdns
echo.

echo [3/3] Renewing IP address...
echo (Please wait, virtual adapters may take a moment)
echo ----------------------------------------------------------
ipconfig /renew
echo.

echo ==========================================================
echo      Network refresh complete! Closing in 5 seconds.      
echo ==========================================================
timeout /t 5
exit