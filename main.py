import os
import sys
import ctypes
import webview
from backend.network_manager import NetworkManager
from backend.updater import UpdateManager

# ==========================================
# SILENT AUTO-ADMIN ELEVATION
# ==========================================
def is_admin():
    """Check if the script is running with Windows Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

if not is_admin():
    # Force the app to relaunch using 'pythonw.exe' (Windowed Python)
    # This triggers the Admin UAC prompt but completely hides the background terminal.
    executable = sys.executable
    if executable.lower().endswith("python.exe"):
        executable = executable.replace("python.exe", "pythonw.exe")
    
    ctypes.windll.shell32.ShellExecuteW(
        None, 
        "runas", 
        executable, 
        f'"{os.path.abspath(__file__)}"', 
        None, 
        1 
    )
    sys.exit()
# ==========================================

class BridgeAPI:
    def set_dns(self, primary: str, secondary: str | None = None):
        return NetworkManager.set_dns(primary, secondary)

    def quick_refresh(self):
        return NetworkManager.quick_refresh()

    def deep_repair(self):
        return NetworkManager.deep_repair()

    def get_current_dns(self):
        return NetworkManager.get_current_dns()

    def run_ping_diagnostics(self):
        return NetworkManager.run_ping_diagnostics()

    def run_speedtest(self, server_id: str | None = None):
        return NetworkManager.run_speedtest(server_id)

    def check_updates(self):
        return UpdateManager.check_for_updates()

    def apply_update(self, url: str):
        return UpdateManager.apply_update(url)

def main():
    api = BridgeAPI()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_path = os.path.join(current_dir, "frontend", "index.html")
    
    webview.create_window(
        title="Network Toolkit",
        url=frontend_path,
        js_api=api,
        width=1050,
        height=700,
        resizable=True,
        min_size=(900, 600)
    )
    webview.start()

if __name__ == "__main__":
    main()