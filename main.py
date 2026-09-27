import os
import sys
import ctypes
import webview
from backend.network_manager import NetworkManager
from backend.updater import UpdateManager

# ==========================================
# ADMIN PERMISSION CHECK (RUNS FIRST)
# ==========================================
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except: return False

if not is_admin():
    executable = sys.executable
    if executable.lower().endswith("python.exe"):
        executable = executable.replace("python.exe", "pythonw.exe")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, f'"{os.path.abspath(__file__)}"', None, 1)
    sys.exit()

class BridgeAPI:
    def set_dns(self, primary: str, secondary: str | None = None): return NetworkManager.set_dns(primary, secondary)
    def quick_refresh(self): return NetworkManager.quick_refresh()
    def deep_repair(self): return NetworkManager.deep_repair()
    def get_current_dns(self): return NetworkManager.get_current_dns()
    def get_isp_info(self): return NetworkManager.get_isp_info()
    def run_ping_diagnostics(self): return NetworkManager.run_ping_diagnostics()
    def run_speedtest(self, server_type: str = "bdix"): return NetworkManager.run_speedtest(server_type)
    def load_history(self): return NetworkManager.get_history()
    def save_history(self, history_data): return NetworkManager.save_history(history_data)
    def clear_history(self): return NetworkManager.clear_history()
    def check_updates(self): return UpdateManager.check_for_updates()
    def apply_update(self, url: str): return UpdateManager.apply_update(url)

def main():
    api = BridgeAPI()
    
    # Resolve the correct path whether running as raw Python or compiled .exe
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    frontend_path = os.path.join(base_dir, "frontend", "index.html")
    
    webview.create_window(
        "Network Toolkit v1.1.0", 
        url=frontend_path, 
        js_api=api, 
        width=1050, 
        height=750, 
        resizable=True
    )
    webview.start()

if __name__ == "__main__":
    main()