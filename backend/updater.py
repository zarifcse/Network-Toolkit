import os
import sys
import subprocess
import requests

GITHUB_REPO = "zarifcse/Network-Toolkit"
CURRENT_VERSION = "v1.1.0"

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def parse_version(v: str) -> tuple:
    """Converts 'v1.1.0' into numeric tuple (1, 1, 0) for safe comparison."""
    try:
        clean = v.lstrip("v").strip()
        parts = [int(x) for x in clean.split(".") if x.isdigit()]
        return tuple(parts) if parts else (0, 0, 0)
    except Exception:
        return (0, 0, 0)

class UpdateManager:
    @staticmethod
    def check_for_updates() -> dict:
        """Queries GitHub's release endpoint via 302 web-redirect inspection."""
        url = f"https://github.com/{GITHUB_REPO}/releases/latest"
        try:
            resp = requests.get(url, headers=HTTP_HEADERS, allow_redirects=False, timeout=6)
            if resp.status_code in (301, 302):
                redirect_url = resp.headers.get("Location", "")
                latest_version = redirect_url.rstrip("/").split("/")[-1]
                
                if latest_version and parse_version(latest_version) > parse_version(CURRENT_VERSION):
                    download_url = (
                        f"https://github.com/{GITHUB_REPO}/releases/download/"
                        f"{latest_version}/NetworkToolkit.exe"
                    )
                    return {
                        "update_available": True,
                        "latest_version": latest_version,
                        "current_version": CURRENT_VERSION,
                        "download_url": download_url
                    }
        except Exception as e:
            return {"update_available": False, "error": str(e)}

        return {"update_available": False, "current_version": CURRENT_VERSION}

    @staticmethod
    def apply_update(download_url: str) -> dict:
        """Downloads updated binary and uses an unpolluted batch process to swap and elevate."""
        if not getattr(sys, 'frozen', False):
            return {
                "status": "error",
                "message": "Cannot auto-update in Python script mode. Build and run the compiled .exe to test."
            }

        temp_dir = os.environ.get("TEMP", os.getcwd())
        temp_exe = os.path.join(temp_dir, "NetworkToolkit_update.exe")
        current_exe = os.path.abspath(sys.executable)
        exe_filename = os.path.basename(current_exe)
        bat_path = os.path.join(temp_dir, "network_toolkit_updater.bat")
        log_file = os.path.join(temp_dir, "network_toolkit_update.log")

        try:
            # 1. Download updated binary
            with requests.get(download_url, headers=HTTP_HEADERS, stream=True, timeout=25) as r:
                r.raise_for_status()
                with open(temp_exe, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)

            # 2. Verify payload size
            if not os.path.exists(temp_exe) or os.path.getsize(temp_exe) < 3 * 1024 * 1024:
                if os.path.exists(temp_exe):
                    os.remove(temp_exe)
                return {"status": "error", "message": "Incomplete download package from GitHub."}

            # 3. Create native batch script with stripped PyInstaller environment
            bat_content = f"""@echo off
set "LOG={log_file}"
set "TARGET={current_exe}"
set "SOURCE={temp_exe}"
set "EXE_NAME={exe_filename}"

:: Explicitly strip PyInstaller inherited environment variables
set "_PYI_PARENT_PID="
set "_MEIPASS2="
set "_PYI_SPLASH_IPC="
set "_PYI_PROCNAME="

echo [START] Updater initiated at %TIME% > "%LOG%"

:: Wait 2 seconds for Python process to release immediate handles
ping 127.0.0.1 -n 3 >nul

:: Wait until ALL PyInstaller parent bootloader instances are dead
:ProcessWait
tasklist /fi "imagename eq %EXE_NAME%" | findstr /i "%EXE_NAME%" >nul
if not errorlevel 1 (
    echo [WAIT] Waiting for %EXE_NAME% to terminate... >> "%LOG%"
    ping 127.0.0.1 -n 2 >nul
    goto ProcessWait
)
echo [PROCESS] All instances cleared >> "%LOG%"

:: Overwrite with a retry loop (up to 15 attempts)
:CopyLoop
echo [COPY] Attempting move... >> "%LOG%"
move /y "%SOURCE%" "%TARGET%" >> "%LOG%" 2>&1
if exist "%SOURCE%" (
    echo [LOCKED] File locked, retrying in 1s... >> "%LOG%"
    ping 127.0.0.1 -n 2 >nul
    goto CopyLoop
)
echo [SUCCESS] File replaced successfully >> "%LOG%"

:: Ensure environment is clean immediately before relaunch
set "_PYI_PARENT_PID="
set "_MEIPASS2="
set "_PYI_SPLASH_IPC="
set "_PYI_PROCNAME="

echo [LAUNCH] Starting updated executable... >> "%LOG%"
start "" "%TARGET%"
echo [DONE] Updater finished >> "%LOG%"

:: Self delete
del "%~f0"
"""
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)

            # 4. Clean environment in Python before spawning cmd.exe
            clean_env = os.environ.copy()
            for key in list(clean_env.keys()):
                if key.startswith("_PYI") or key.startswith("_MEI"):
                    clean_env.pop(key, None)

            # Launch detached cmd.exe with scrubbed environment
            subprocess.Popen(
                ["cmd.exe", "/c", bat_path],
                env=clean_env,
                creationflags=0x08000000 | 0x00000200
            )

            # 5. Immediate process termination
            os._exit(0)

        except Exception as e:
            if os.path.exists(temp_exe):
                try:
                    os.remove(temp_exe)
                except OSError:
                    pass
            return {"status": "error", "message": str(e)}