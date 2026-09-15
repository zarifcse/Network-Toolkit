@echo off
:: Force Windows to keep the script in its current directory
cd /d "%~dp0"
title BDIX and Raw Internet Speed Test Tool
cls

echo ==========================================================
echo            BDIX and RAW INTERNET SPEED TESTER             
echo ==========================================================
echo.

:: Safely check for official Ookla Speedtest CLI; download locally if missing
if not exist "speedtest.exe" (
    echo [Setup] Official Ookla Speedtest CLI not found in this folder.
    echo [Setup] Safely downloading CLI directly from Ookla's servers...
    powershell -Command "Invoke-WebRequest 'https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-win64.zip' -OutFile 'speedtest-cli.zip'"
    echo [Setup] Extracting tool...
    powershell -Command "Expand-Archive -Path 'speedtest-cli.zip' -DestinationPath '.' -Force"
    del "speedtest-cli.zip" >nul 2>&1
    del "speedtest.md" >nul 2>&1
    del "speedtest.5" >nul 2>&1
    echo [Setup] Complete!
    echo.
)

:: Test 1: BDIX Speed Test (Auto-Selects Closest Local Peering Server)
echo ----------------------------------------------------------
echo [1/2] TESTING BDIX SPEED (Local Peering - Dhaka)
echo ----------------------------------------------------------
echo Target: Auto-selecting lowest ping local Dhaka/BDIX server...
echo Measuring local BDIX bandwidth...
echo.
speedtest.exe --accept-license --accept-gdpr
echo.

:: Test 2: Raw / International Speed Test (Singtel Singapore Gateway)
echo ----------------------------------------------------------
echo [2/2] TESTING RAW SPEED (International - Singapore)
echo ----------------------------------------------------------
echo Target: Singtel Singapore (Server ID: 13623)
echo Measuring global cable bandwidth...
echo.
speedtest.exe -s 13623
echo.

echo ==========================================================
echo               All speed tests completed!                  
echo ==========================================================
pause
exit