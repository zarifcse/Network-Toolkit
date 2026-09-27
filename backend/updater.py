import os
import sys
import base64
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
        Streams new binary, performs payload validation, clears running file locks,
        retries replacement up to 10 times, and relaunches with UAC elevation.
        """
        # Safety Guard: Never allow script-mode testing to overwrite python.exe
        if not getattr(sys, 'frozen', False):
            return {
                "status": "error",
                "message": "Auto-update only runs from the compiled .exe, not in Python script mode."
            }

        temp_dir = os.environ.get("TEMP", os.getcwd())
        temp_exe = os.path.join(temp_dir, "NetworkToolkit_update.exe")
        current_exe = os.path.abspath(sys.executable)
        exe_name = os.path.splitext(os.path.basename(current_exe))[0]
        log_file = os.path.join(temp_dir, "network_toolkit_update.log")

        try:
            # 1. Stream download with connection and chunk timeouts
            with requests.get(download_url, headers=HTTP_HEADERS, stream=True, timeout=20) as r:
                r.raise_for_status()
                with open(temp_exe, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)

            # 2. Payload integrity check (must exist and be > 3MB for a PyInstaller bundle)
            if not os.path.exists(temp_exe) or os.path.getsize(temp_exe) < 3 * 1024 * 1024:
                if os.path.exists(temp_exe):
                    os.remove(temp_exe)
                return {"status": "error", "message": "Incomplete or corrupted download package from GitHub."}

            # 3. Robust, decoupled PowerShell hand-off:
            # - Waits up to 15s for all processes bearing this binary's name to exit
            # - Retries file swap up to 10 times (500ms intervals) to handle antivirus file holds
            # - Re-elevates with -Verb RunAs for UAC admin rights
            # - Logs step status directly to %TEMP%\network_toolkit_update.log
            ps_script = (
                f"$log = '{log_file}'; "
                f"'[START] Update hand-off initiated' | Out-File $log; "
                f"$timeout = 15; $sw = [System.Diagnostics.Stopwatch]::StartNew(); "
                f"while ((Get-Process -Name '{exe_name}' -ErrorAction SilentlyContinue) -and ($sw.Elapsed.TotalSeconds -lt $timeout)) {{ "
                f"  Start-Sleep -Milliseconds 300; "
                f"}} "
                f"'[PROCESS] All process instances cleared' | Out-File $log -Append; "
                f"$replaced = $false; "
                f"for ($i = 0; $i -lt 10; $i++) {{ "
                f"  try {{ "
                f"    Copy-Item -LiteralPath '{temp_exe}' -Destination '{current_exe}' -Force -ErrorAction Stop; "
                f"    Remove-Item -LiteralPath '{temp_exe}' -Force -ErrorAction SilentlyContinue; "
                f"    $replaced = $true; "
                f"    '[COPIED] Executable replaced successfully' | Out-File $log -Append; "
                f"    break; "
                f"  }} catch {{ "
                f"    Start-Sleep -Milliseconds 500; "
                f"  }} "
                f"}} "
                f"if ($replaced) {{ "
                f"  '[LAUNCH] Relaunching application with admin privileges' | Out-File $log -Append; "
                f"  Start-Process -FilePath '{current_exe}' -Verb RunAs; "
                f"}} else {{ "
                f"  '[ERROR] Failed to overwrite binary file' | Out-File $log -Append; "
                f"}}"
            )
            encoded_cmd = base64.b64encode(ps_script.encode('utf-16le')).decode('ascii')

            subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-EncodedCommand", encoded_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW | 0x00000008  # DETACHED_PROCESS
            )

            # 4. Immediate kernel exit to clear the current executable file lock
            os._exit(0)

        except Exception as e:
            if os.path.exists(temp_exe):
                try:
                    os.remove(temp_exe)
                except OSError:
                    pass
            return {"status": "error", "message": f"Update failed: {str(e)}"}