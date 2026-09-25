import os
import json
import urllib.request
import zipfile
import subprocess
import threading
import base64
import socket

class NetworkManager:
    # Strict Thread Lock prevents Ookla from issuing a "Too Many Requests" IP ban
    _speedtest_queue_lock = threading.Lock()

    @staticmethod
    def run_command(cmd: str) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)

    # ==========================================
    # DNS PROFILES
    # ==========================================
    @classmethod
    def set_dns(cls, primary: str, secondary: str | None = None) -> dict:
        if primary.lower() == "dhcp":
            cmd = "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Get-WmiObject Win32_NetworkAdapterConfiguration -Filter 'IPEnabled=True' | Invoke-WmiMethod -Name SetDNSServerSearchOrder\""
        else:
            sec_str = f", '{secondary}'" if secondary else ""
            cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -Command \"Get-WmiObject Win32_NetworkAdapterConfiguration -Filter 'IPEnabled=True' | Invoke-WmiMethod -Name SetDNSServerSearchOrder -ArgumentList @(,'{primary}'{sec_str})\""
        
        success, out = cls.run_command(cmd)
        cls.run_command("ipconfig /flushdns")
        if success: return {"status": "success", "message": "DNS settings applied."}
        return {"status": "error", "message": "Failed. Admin privileges required."}

    @classmethod
    def get_current_dns(cls) -> dict:
        ps_cmd = "(Get-WmiObject Win32_NetworkAdapterConfiguration -Filter 'IPEnabled=True' | Where-Object {$_.DNSServerSearchOrder -ne $null} | Select-Object -ExpandProperty DNSServerSearchOrder) -join ', '"
        success, out = cls.run_command(f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{ps_cmd}"')
        if success and out.strip(): return {"status": "success", "message": f"Active DNS: {out.strip()}"}
        return {"status": "success", "message": "Active DNS: Automatic (DHCP)"}

    # ==========================================
    # SYSTEM REPAIRS
    # ==========================================
    @classmethod
    def quick_refresh(cls) -> dict:
        cls.run_command("ipconfig /release")
        cls.run_command("ipconfig /renew")
        cls.run_command("ipconfig /flushdns")
        return {"status": "success", "message": "Network refreshed."}

    @classmethod
    def deep_repair(cls) -> dict:
        for cmd in ["ipconfig /release", "ipconfig /flushdns", "netsh winsock reset", "netsh int ip reset", "ipconfig /renew"]:
            cls.run_command(cmd)
        return {"status": "success", "message": "Deep repair complete. Restart recommended."}

    # ==========================================
    # LIVE ISP & NETWORK INFORMATION
    # ==========================================
    @classmethod
    def get_isp_info(cls) -> dict:
        data = {
            "status": "Online", "type": "Unknown", "adapter": "Unknown",
            "local_ipv4": "Unknown", "public_ip": "Fetching...",
            "gateway": "Unknown", "dns": "Unknown",
            "isp_name": "Unknown", "location": "Unknown"
        }

        # 1. Native OS Socket Probe: Identifies the active outbound interface IP immediately
        active_local_ip = "Unknown"
        try:
            probe_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            probe_sock.connect(("8.8.8.8", 80))
            active_local_ip = probe_sock.getsockname()[0]
            probe_sock.close()
            data["local_ipv4"] = active_local_ip
        except Exception:
            pass

        # 2. Kernel WMI Engine: Matches the IP strictly to the Hardware Configuration
        ps_script = f"""
        $ErrorActionPreference = 'SilentlyContinue'
        $activeIp = '{active_local_ip}'
        
        $config = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" | Where-Object {{ $_.IPAddress -contains $activeIp }} | Select-Object -First 1

        if (-not $config) {{
            $config = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" | Where-Object {{ $_.DefaultIPGateway -ne $null }} | Select-Object -First 1
        }}

        if ($config) {{
            $adapter = Get-WmiObject Win32_NetworkAdapter -Filter "Index = $($config.Index)" | Select-Object -First 1
            $desc = if ($adapter -and $adapter.Name) {{ $adapter.Name }} else {{ $config.Description }}
            $type = if ($desc -match 'Wi-Fi|Wireless|802.11|WLAN') {{ 'Wi-Fi' }} else {{ 'Ethernet' }}
            
            $ipv4 = if ($activeIp -ne 'Unknown') {{ $activeIp }} else {{ $config.IPAddress[0] }}
            $gw = if ($config.DefaultIPGateway) {{ $config.DefaultIPGateway[0] }} else {{ 'Unknown' }}
            $dns = if ($config.DNSServerSearchOrder) {{ $config.DNSServerSearchOrder -join ', ' }} else {{ 'Automatic (DHCP)' }}

            @{{ Adapter=$desc; Type=$type; IPv4=$ipv4; GW=$gw; DNS=$dns }} | ConvertTo-Json -Compress
        }} else {{
            @{{ Adapter='Unknown'; Type='Unknown'; IPv4=$activeIp; GW='Unknown'; DNS='Automatic (DHCP)' }} | ConvertTo-Json -Compress
        }}
        """

        encoded_ps = base64.b64encode(ps_script.encode('utf-16le')).decode('utf-8')
        success, out = cls.run_command(f"powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand {encoded_ps}")
        
        if success and out.strip():
            try:
                local_data = json.loads(out.strip())
                data["adapter"] = local_data.get("Adapter", "Unknown")
                data["type"] = local_data.get("Type", "Unknown")
                data["local_ipv4"] = local_data.get("IPv4", active_local_ip)
                data["gateway"] = local_data.get("GW", "Unknown")
                data["dns"] = local_data.get("DNS", "Unknown") if local_data.get("DNS") else "Automatic (DHCP)"
            except Exception:
                pass

        # 3. Public IP and Retail Provider Identification (Restored to ipinfo.io)
        try:
            req = urllib.request.Request("https://ipinfo.io/json", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                ipinfo = json.loads(response.read().decode())
                data["public_ip"] = ipinfo.get("ip", "Unknown")
                org = ipinfo.get("org", "Unknown")
                if " " in org and org.startswith("AS"):
                    org = org.split(" ", 1)[1]
                data["isp_name"] = org
                data["location"] = f"{ipinfo.get('city', 'Unknown')}, {ipinfo.get('country', 'Unknown')}"
        except Exception:
            # Fallback if ipinfo.io cannot be reached
            try:
                req = urllib.request.Request("http://ip-api.com/json/?fields=status,country,city,isp,org,query", headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    fallback_info = json.loads(response.read().decode())
                    data["public_ip"] = fallback_info.get("query", "Unknown")
                    data["isp_name"] = fallback_info.get("org") or fallback_info.get("isp", "Unknown")
                    data["location"] = f"{fallback_info.get('city', 'Unknown')}, {fallback_info.get('country', 'Unknown')}"
            except Exception:
                data["status"] = "Offline"

        return data

    # ==========================================
    # ROUTING TELEMETRY
    # ==========================================
    @classmethod
    def run_ping_diagnostics(cls) -> list[dict]:
        router_ip, isp_gw = "Unknown", "Unknown"
        success, out = cls.run_command("tracert -d -h 2 -w 500 8.8.8.8")
        if success:
            lines = [line.strip() for line in out.splitlines() if line.strip() and not line.startswith("Tracing")]
            for line in lines:
                parts = line.split()
                if len(parts) > 0 and parts[0] == "1": router_ip = parts[-1]
                elif len(parts) > 0 and parts[0] == "2": isp_gw = parts[-1] if "Request timed out" not in line else "Hidden by ISP"

        targets = [
            {"name": "Local Router Gateway", "ip": router_ip},
            {"name": "ISP Next-Hop Gateway", "ip": isp_gw},
            {"name": "Google DNS", "ip": "8.8.8.8"},
            {"name": "Cloudflare DNS", "ip": "1.1.1.1"},
            {"name": "Quad9 Primary", "ip": "9.9.9.9"},
            {"name": "Singapore Game Cluster", "ip": "13.228.0.251"},
        ]
        
        results = []
        for target in targets:
            if target["ip"] in ["Unknown", "Hidden by ISP"]:
                results.append({"name": target["name"], "ip": target["ip"], "latency": "N/A", "packet_loss": "N/A"})
                continue
                
            _, out = cls.run_command(f"ping -n 4 -w 1000 {target['ip']}")
            latency, loss = "Timeout", "100%"
            for line in out.splitlines():
                if "Average =" in line: latency = line.split("Average =")[-1].strip()
                if "Lost =" in line and "(" in line: loss = line.split("(")[-1].split("loss")[0].strip()

            results.append({"name": target["name"], "ip": target["ip"], "latency": latency, "packet_loss": loss})
        return results

    # ==========================================
    # BANDWIDTH MEASUREMENT (QUEUED)
    # ==========================================
    @classmethod
    def run_speedtest(cls, target: str) -> dict:
        app_dir = os.path.join(os.environ["LOCALAPPDATA"], "NetworkToolkit")
        os.makedirs(app_dir, exist_ok=True)
        base_exe = os.path.join(app_dir, "speedtest.exe")

        with cls._speedtest_queue_lock:
            if not os.path.exists(base_exe):
                zip_url = "https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-win64.zip"
                zip_dest = os.path.join(app_dir, "speedtest.zip")
                req = urllib.request.Request(zip_url, headers={'User-Agent': 'Mozilla/5.0'})
                try:
                    with urllib.request.urlopen(req, timeout=15) as response, open(zip_dest, 'wb') as out_file:
                        import shutil
                        shutil.copyfileobj(response, out_file)
                    with zipfile.ZipFile(zip_dest, "r") as zip_ref: 
                        zip_ref.extractall(app_dir)
                    if os.path.exists(zip_dest): os.remove(zip_dest)
                except Exception as e:
                    return {"status": "error", "message": f"Download failed: {str(e)}"}
            
            cmd = [base_exe, "--format=json", "--accept-license", "--accept-gdpr"]
            
            if target == "singapore":
                cmd.extend(["-s", "13623"])

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
                out = result.stdout
                err = result.stderr
                
                if "Too many requests" in out or "Too many requests" in err:
                    return {"status": "error", "message": "Ookla Anti-Spam: Please wait 60 seconds before testing again."}
                
                if not out.strip():
                    return {"status": "error", "message": f"No output. Error: {err.strip()}"}

                for line in out.splitlines():
                    line = line.strip()
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            data = json.loads(line)
                            if "error" in data or data.get("type") == "log":
                                msg = data.get("message", "Server timed out.")
                                if "NoServersException" in msg:
                                    msg = "Target server is currently offline for maintenance."
                                return {"status": "error", "message": msg}
                                
                            return {
                                "status": "success",
                                "download_mbps": round(data["download"]["bandwidth"] * 8 / 1_000_000, 2),
                                "upload_mbps": round(data["upload"]["bandwidth"] * 8 / 1_000_000, 2),
                                "ping_ms": round(data["ping"]["latency"], 1),
                                "server": f"{data['server'].get('sponsor', data['server'].get('name'))} ({data['server']['location']})"
                            }
                        except Exception:
                            continue
                
                return {"status": "error", "message": "Failed to parse test results."}
            except Exception as e:
                return {"status": "error", "message": f"Execution failed: {str(e)}"}

    # ==========================================
    # HISTORY STORAGE
    # ==========================================
    @classmethod
    def get_history(cls) -> dict:
        app_dir = os.path.join(os.environ["LOCALAPPDATA"], "NetworkToolkit")
        history_file = os.path.join(app_dir, "history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f: return json.load(f)
            except Exception: pass
        return {"speed": [], "ping": []}

    @classmethod
    def save_history(cls, data: dict):
        app_dir = os.path.join(os.environ["LOCALAPPDATA"], "NetworkToolkit")
        history_file = os.path.join(app_dir, "history.json")
        with open(history_file, "w") as f: json.dump(data, f)
        return {"status": "success"}

    @classmethod
    def clear_history(cls):
        app_dir = os.path.join(os.environ["LOCALAPPDATA"], "NetworkToolkit")
        history_file = os.path.join(app_dir, "history.json")
        if os.path.exists(history_file): os.remove(history_file)
        return {"status": "success"}