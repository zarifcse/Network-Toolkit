import os
import subprocess
import sys
import requests

GITHUB_REPO = "zarifcse/Network-Toolkit"
CURRENT_VERSION = "v1.1.1"

def parse_version(v: str) -> tuple:
    """Converts 'v1.1.0' into a numeric tuple (1, 1, 0) for accurate comparison."""
    try:
        clean = v.lstrip("v").strip()
        return tuple(int(x) for x in clean.split(".") if x.isdigit())
    except Exception:
        return (0, 0, 0)

class UpdateManager:
    @staticmethod
    def check_for_updates() -> dict:
        """Query the GitHub Releases API for a newer version tag."""
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                return {"update_available": False, "message": "Up to date."}
            
            data = resp.json()
            latest_version = data.get("tag_name", "")
            
            # Strict version comparison: Only trigger if GitHub release is strictly GREATER
            if latest_version and parse_version(latest_version) > parse_version(CURRENT_VERSION):
                exe_asset = next((a for a in data.get("assets", []) if a["name"].endswith(".exe")), None)
                if exe_asset:
                    return {
                        "update_available": True,
                        "latest_version": latest_version,
                        "current_version": CURRENT_VERSION,
                        "download_url": exe_asset["browser_download_url"]
                    }
        except Exception as e:
            return {"update_available": False, "error": str(e)}

        return {"update_available": False, "current_version": CURRENT_VERSION}

    @staticmethod
    def apply_update(download_url: str):
        """Downloads the new binary and spins off a bulletproof background process to replace it."""
        temp_exe = os.path.join(os.environ["TEMP"], "NetworkToolkit_new.exe")
        
        # 1. Download the new file to a temporary location
        r = requests.get(download_url, stream=True)
        with open(temp_exe, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        current_exe = sys.executable
        
        # 2. Create a bulletproof updater script with a Retry Loop
        bat_path = os.path.join(os.environ["TEMP"], "network_toolkit_updater.bat")
        bat_content = f"""@echo off
:WaitLoop
timeout /t 1 /nobreak >nul
del "{current_exe}" >nul 2>&1
if exist "{current_exe}" goto WaitLoop

move /y "{temp_exe}" "{current_exe}" >nul 2>&1
start "" "{current_exe}"
del "%~f0"
"""
        with open(bat_path, "w") as bat_file:
            bat_file.write(bat_content)
        
        # 3. Launch the script completely detached from the main application
        # 0x08000000 = CREATE_NO_WINDOW
        # 0x00000008 = DETACHED_PROCESS (Ensures the script survives when the app dies)
        subprocess.Popen(
            ["cmd.exe", "/c", bat_path],
            creationflags=0x08000000 | 0x00000008
        )
        
        # 4. Instantly kill this program to release the Windows file lock immediately
        os._exit(0)