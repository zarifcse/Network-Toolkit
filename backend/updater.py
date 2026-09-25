import os
import subprocess
import sys
import requests

GITHUB_REPO = "zarifcse/Network-Toolkit"
CURRENT_VERSION = "v1.1.1"

def parse_version(v: str) -> tuple:
    """Converts 'v1.1.1' into a numeric tuple (1, 1, 1) for accurate comparison."""
    try:
        clean = v.lstrip("v").strip()
        return tuple(int(x) for x in clean.split(".") if x.isdigit())
    except Exception:
        return (0, 0, 0)

class UpdateManager:
    @staticmethod
    def check_for_updates() -> dict:
        """
        Query standard GitHub web routes instead of the API.
        This completely bypasses the 60 requests/hour API rate limit.
        """
        # Notice we removed "api." and changed the path to the standard web releases page
        url = f"https://github.com/{GITHUB_REPO}/releases/latest"
        
        try:
            # allow_redirects=False captures the 302 Redirect header without downloading the webpage
            resp = requests.get(url, allow_redirects=False, timeout=5)
            
            if resp.status_code == 302:
                redirect_url = resp.headers.get("Location", "")
                
                # The redirect URL ends with the tag name (e.g., .../releases/tag/v1.1.1)
                latest_version = redirect_url.split("/")[-1]
                
                # Strict version comparison
                if latest_version and parse_version(latest_version) > parse_version(CURRENT_VERSION):
                    # Hardcode the expected asset download URL structure
                    download_url = f"https://github.com/{GITHUB_REPO}/releases/download/{latest_version}/NetworkToolkit.exe"
                    
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
        subprocess.Popen(
            ["cmd.exe", "/c", bat_path],
            creationflags=0x08000000 | 0x00000008
        )
        
        # 4. Instantly kill this program to release the Windows file lock immediately
        os._exit(0)