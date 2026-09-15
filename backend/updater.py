import os
import subprocess
import sys
import requests

# Link to your repository
GITHUB_REPO = "zarifcse/Network-Toolkit"
CURRENT_VERSION = "v1.0.0"

class UpdateManager:
    @staticmethod
    def check_for_updates() -> dict:
        """Query the GitHub Releases API for a newer version tag."""
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        try:
            # We fetch the latest release published on GitHub
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                return {"update_available": False, "message": "Up to date."}
            
            data = resp.json()
            latest_version = data.get("tag_name", "")
            
            if latest_version and latest_version != CURRENT_VERSION:
                # Find the attached .exe file in the release assets
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
        """Downloads the new binary and spins off a background process to replace it."""
        temp_exe = os.path.join(os.environ["TEMP"], "NetworkToolkit_new.exe")
        
        # Download the new file to a temporary location
        r = requests.get(download_url, stream=True)
        with open(temp_exe, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # To avoid the Windows file lock, we run a detached PowerShell command 
        # to wait 2 seconds, replace the executable, and start the new one.
        current_exe = sys.executable
        swap_script = (
            f"Start-Sleep -Seconds 2; "
            f"Move-Item -Force -Path '{temp_exe}' -Destination '{current_exe}'; "
            f"Start-Process -FilePath '{current_exe}'"
        )
        
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", swap_script],
            creationflags=0x08000000 # CREATE_NO_WINDOW
        )
        
        # Immediately exit the current app to release the file lock
        sys.exit(0)