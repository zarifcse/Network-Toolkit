import ctypes
import json
import os
import subprocess
import urllib.request
import zipfile

# Flag to prevent terminal windows from popping up
CREATE_NO_WINDOW = 0x08000000

class NetworkManager:
    @staticmethod
    def is_admin() -> bool:
        """Check if application has elevated administrative privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @staticmethod
    def run_command(command: str) -> tuple[bool, str]:
        """Execute system commands silently in the background."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stdout.strip()
        except Exception as ex:
            return False, str(ex)

    @classmethod
    def set_dns(cls, primary: str, secondary: str | None = None) -> dict:
        """Configure DNS servers on active physical network adapters."""
        if not cls.is_admin():
            return {"status": "error", "message": "Administrator privileges required."}

        if primary.lower() == "dhcp":
            ps_cmd = (
                "Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' } | "
                "Set-DnsClientServerAddress -ResetServerAddresses"
            )
        else:
            addrs = f"'{primary}'" if not secondary else f"'{primary}', '{secondary}'"
            ps_cmd = (
                f"Get-NetAdapter -Physical | Where-Object {{ $_.Status -eq 'Up' }} | "
                f"Set-DnsClientServerAddress -ServerAddresses ({addrs})"
            )

        success, out = cls.run_command(f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{ps_cmd}"')
        cls.run_command("ipconfig /flushdns")

        return {
            "status": "success" if success else "error",
            "message": "DNS settings updated successfully." if success else out
        }

    @classmethod
    def get_current_dns(cls) -> dict:
        """Fetch the currently active DNS IPs for physical adapters."""
        ps_cmd = (
            "(Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' } | "
            "Get-DnsClientServerAddress -AddressFamily IPv4).ServerAddresses -join ', '"
        )
        success, out = cls.run_command(f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{ps_cmd}"')
        
        if success and out.strip():
            return {"status": "success", "message": f"Active DNS: {out.strip()}"}
        return {"status": "success", "message": "Active DNS: Automatic (DHCP)"}

    @classmethod
    def quick_refresh(cls) -> dict:
        """Release IP, flush resolver cache, and renew IP."""
        cls.run_command("ipconfig /release")
        cls.run_command("ipconfig /flushdns")
        cls.run_command("ipconfig /renew")
        return {"status": "success", "message": "Network configuration refreshed."}

    @classmethod
    def deep_repair(cls) -> dict:
        """Reset Winsock, TCP/IP stack, ARP cache, and NetBIOS."""
        if not cls.is_admin():
            return {"status": "error", "message": "Administrator privileges required."}

        cls.run_command("ipconfig /release")
        cls.run_command("ipconfig /flushdns")
        cls.run_command("arp -d *")
        cls.run_command("nbtstat -R")
        cls.run_command("nbtstat -RR")
        cls.run_command("netsh winsock reset")
        cls.run_command("netsh int ip reset")
        cls.run_command("ipconfig /renew")
        return {"status": "success", "message": "Deep network repair completed successfully."}

    @classmethod
    def run_ping_diagnostics(cls) -> list[dict]:
        """Ping targeted DNS and gaming server endpoints."""
        targets = [
            {"name": "Quad9 Primary", "ip": "9.9.9.9"},
            {"name": "Cloudflare DNS", "ip": "1.1.1.1"},
            {"name": "Google DNS", "ip": "8.8.8.8"},          
            {"name": "ISP Cache DNS", "ip": "10.11.12.13"},
            {"name": "Singapore Game Cluster", "ip": "13.228.0.251"},
        ]
        results = []
        for target in targets:
            _, out = cls.run_command(f"ping -n 4 {target['ip']}")
            latency = "Timeout"
            loss = "100%"

            for line in out.splitlines():
                if "Average =" in line:
                    latency = line.split("Average =")[-1].strip()
                if "Lost =" in line and "(" in line:
                    loss = line.split("(")[-1].split("loss")[0].strip()

            results.append({
                "name": target["name"],
                "ip": target["ip"],
                "latency": latency,
                "packet_loss": loss
            })
        return results

    @classmethod
    def run_speedtest(cls, server_id: str | None = None) -> dict:
        """Ensure Ookla CLI exists locally and execute speed test."""
        cli_exe = os.path.join(os.getcwd(), "speedtest.exe")

        if not os.path.exists(cli_exe):
            zip_url = "https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-win64.zip"
            zip_dest = os.path.join(os.getcwd(), "speedtest-cli.zip")
            urllib.request.urlretrieve(zip_url, zip_dest)
            with zipfile.ZipFile(zip_dest, "r") as zip_ref:
                zip_ref.extractall(os.getcwd())
            if os.path.exists(zip_dest):
                os.remove(zip_dest)

        cmd = f'"{cli_exe}" --format=json --accept-license --accept-gdpr'
        if server_id:
            cmd += f" -s {server_id}"

        _, out = cls.run_command(cmd)
        try:
            data = json.loads(out)
            return {
                "status": "success",
                "download_mbps": round(data["download"]["bandwidth"] * 8 / 1_000_000, 2),
                "upload_mbps": round(data["upload"]["bandwidth"] * 8 / 1_000_000, 2),
                "ping_ms": round(data["ping"]["latency"], 1),
                "server": f"{data['server']['name']} ({data['server']['location']})"
            }
        except Exception:
            return {"status": "error", "message": "Failed to run speed test or parse results."}