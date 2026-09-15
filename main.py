import os
import webview
from backend.network_manager import NetworkManager
from backend.updater import UpdateManager

class BridgeAPI:
    """This class exposes Python methods to the JavaScript frontend."""
    def set_dns(self, primary: str, secondary: str | None = None):
        return NetworkManager.set_dns(primary, secondary)

    def quick_refresh(self):
        return NetworkManager.quick_refresh()

    def deep_repair(self):
        return NetworkManager.deep_repair()

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
    
    # Get the absolute path to your HTML file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_path = os.path.join(current_dir, "frontend", "index.html")
    
    # Create the native Windows GUI using Edge WebView2
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