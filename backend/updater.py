import os
import sys
import subprocess
import requests

GITHUB_REPO = "zarifcse/Network-Toolkit"
CURRENT_VERSION = "v1.1.1"

# Standard browser User-Agent to prevent GitHub web route 403 blocks
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def parse_version(v: str) -> tuple:
    """Converts version strings like 'v1.1.1' into numeric tuples (1, 1, 1)."""
    try:
        clean = v.lstrip("v").strip()
        parts = [int(x) for x in clean.split(".") if x.isdigit()]
        return tuple(parts) if parts else (0, 0, 0)
    except Exception:
        return (0, 0, 0)

class UpdateManager:
    @staticmethod
    def check_for_updates() -> dict:
        """
        Queries GitHub's release endpoint via 302 web-redirect inspection.
        Completely bypasses GitHub API 60 req/hour rate limits without tokens.
        """
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
        """
        Streams the new binary with strict timeouts, validates payload size,
        and initiates a PID-targeted PowerShell hand-off before exiting.
        """
        temp_dir = os.environ.get("TEMP", os.getcwd())
        temp_exe = os.path.join(temp_dir, "NetworkToolkit_update.exe")
        current_exe = os.path.abspath(sys.executable)
        current_pid = os.getpid()

        try:
            # 1. Stream download with connection and chunk timeouts
            with requests.get(download_url, headers=HTTP_HEADERS, stream=True, timeout=15) as r:
                r.raise_for_status()
                with open(temp_exe, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)

            # 2. Payload integrity check (must exist and be > 3MB for a PyInstaller bundle)
            if not os.path.exists(temp_exe) or os.path.getsize(temp_exe) < 3 * 1024 * 1024:
                if os.path.exists(temp_exe):
                    os.remove(temp_exe)
                return {"status": "error", "message": "Incomplete or corrupted download."}

            # 3. PID-Targeted PowerShell hand-off:
            # - Waits explicitly for current process PID to clear memory and file locks
            # - Forces binary overwrite
            # - Relaunches the updated executable
            ps_command = (
                f"$ErrorActionPreference = 'Stop'; "
                f"try {{ Wait-Process -Id {current_pid} -Timeout 10 }} catch {{ }}; "
                f"Start-Sleep -Milliseconds 600; "
                f"Move-Item -LiteralPath '{temp_exe}' -Destination '{current_exe}' -Force; "
                f"Start-Process -FilePath '{current_exe}'"
            )

            subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_command],
                creationflags=subprocess.CREATE_NO_WINDOW | 0x00000008  # DETACHED_PROCESS
            )

            # 4. Terminate process immediately to release file lock
            os._exit(0)

        except Exception as e:
            if os.path.exists(temp_exe):
                try:
                    os.remove(temp_exe)
                except OSError:
                    pass
            return {"status": "error", "message": f"Update failed: {str(e)}"}