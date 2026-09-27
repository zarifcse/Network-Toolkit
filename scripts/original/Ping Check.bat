@echo off
title Pre-Game Network and Ping Diagnostic
color 07

echo ================================================================
echo           PRE-GAME NETWORK ^& PING DIAGNOSTIC TOOL
echo ================================================================
echo.

:: 1. Check current active DNS assignments
echo [*] Checking your current active DNS configuration...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-DnsClientServerAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.ServerAddresses -ne $null } | Select-Object -ExpandProperty ServerAddresses" > "%temp%\active_dns.txt"

if exist "%temp%\active_dns.txt" (
    echo Active DNS IPs:
    type "%temp%\active_dns.txt"
    del "%temp%\active_dns.txt"
) else (
    echo [!] Could not retrieve DNS list. Proceeding anyway...
)
echo.

echo ================================================================
echo           TESTING LATENCY AND PACKET LOSS (5 Packets Each)
echo ================================================================
echo.

echo [1/4] Testing Primary DNS (Quad9 - 9.9.9.9)...
ping -n 5 9.9.9.9
echo.

echo [1/4] Testing Primary DNS (Quad9 - 8.8.8.8)...
ping -n 5 8.8.8.8
echo.

echo [1/4] Testing Primary DNS (Cloudflare - 1.1.1.1)...
ping -n 5 1.1.1.1
echo.

echo [2/4] Testing ISP Cache DNS (10.11.12.13)...
ping -n 5 10.11.12.13
echo.

echo [3/4] Testing ISP Cache DNS (103.87.212.10)...
ping -n 5 103.87.212.10
echo.

echo [4/4] Testing Singapore Game Server Cluster (PUBG/LoL/Valorant Route)...
ping -n 5 13.228.0.251
echo.

echo ================================================================
echo                      HOW TO READ RESULTS
echo ================================================================
echo.
echo [1] PACKET LOSS: Check the "Lost = X" count under each test.
echo     - If any test shows 1 or more lost packets, DO NOT play ranked.
echo     - Your ISP's routing table or your local connection is dropping data.
echo.
echo [2] PING STABILITY (Jitter): Compare "Minimum" and "Maximum" ms.
echo     - If the difference is larger than 10-15ms, your line is fluctuating.
echo     - This will feel like micro-stutters in-game. Pause background downloads.
echo.
echo [3] DNS OPTIMIZATION CHECK:
echo     - Ensure both 1.1.1.1 and 10.11.12.13 reply without timeouts. 
echo     - If pinging game servers is fast but you get matchmaking errors, your 
echo       DNS might need to be reset using your Network Optimizer script.
echo.
echo [4] SERVER BASELINES:
echo     - Mumbai expected ping:   ~35ms - 55ms
echo     - Singapore expected ping: ~40ms - 60ms
echo     - If your ping is currently 90ms+ to these servers, your ISP is 
echo       routing traffic poorly right now (peak hour congestion).
echo.
echo ================================================================
echo  Test Completed successfully. Press any key to close this window...
echo ================================================================
pause >nul