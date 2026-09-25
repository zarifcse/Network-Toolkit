const CURRENT_VERSION = "v1.1.1";

// ==========================================
// CORE UI & CONSOLE LOGIC
// ==========================================
function switchTab(tabName) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
  document.getElementById(`tab-${tabName}`).classList.add('active');
  if (event && event.currentTarget) { event.currentTarget.classList.add('active'); }
}

function log(msg) {
  const terminal = document.getElementById('statusConsole');
  const time = new Date().toLocaleTimeString();
  terminal.innerHTML += `<div class="log-line"><span style="color:#64748b;">[${time}]</span> ${msg}</div>`;
  terminal.scrollTop = terminal.scrollHeight; 
}

function copyConsole() {
  const text = document.getElementById('statusConsole').innerText;
  navigator.clipboard.writeText(text);
  log("Console log copied to clipboard.");
}

// ==========================================
// INITIALIZATION & ISP DASHBOARD
// ==========================================
window.addEventListener('pywebviewready', async () => {
  log("System Initialized: Python backend runtime connected.");
  triggerUpdateCheck();
  loadHistory(); 
  loadIspInfo();
});

async function loadIspInfo() {
  document.getElementById('ispStatus').textContent = "Analyzing network...";
  document.getElementById('ispStatus').style.color = "#94a3b8";

  const data = await pywebview.api.get_isp_info();
  
  document.getElementById('ispStatus').textContent = data.status;
  document.getElementById('ispStatus').style.color = data.status === "Online" ? "#4ade80" : "#ef4444";
  
  document.getElementById('ispName').textContent = data.isp_name;
  document.getElementById('ispLoc').textContent = data.location;
  document.getElementById('ispType').textContent = data.type;
  document.getElementById('ispAdapter').textContent = data.adapter;
  document.getElementById('ispIPv4').textContent = data.local_ipv4;
  document.getElementById('ispGw').textContent = data.gateway;
  document.getElementById('ispDns').textContent = data.dns;
  document.getElementById('ispPublic').textContent = data.public_ip;
}

// MANUAL REFRESH HANDLER FOR ISP PANEL
async function refreshIspData() {
  const btn = document.getElementById('ispRefreshBtn');
  if (btn) btn.classList.add('spinning');
  
  log("Querying updated adapter and public ISP telemetry...");
  
  try {
    await loadIspInfo();
    log("Live network data updated successfully.");
  } catch (err) {
    log(`[ERROR] Network refresh failed: ${err}`);
  } finally {
    if (btn) btn.classList.remove('spinning');
  }
}

function toggleIp(id) {
  const el = document.getElementById(id);
  const btn = document.getElementById('toggleIpBtn');
  if (el.classList.contains('blurred')) {
    el.classList.remove('blurred');
    btn.textContent = 'Hide';
  } else {
    el.classList.add('blurred');
    btn.textContent = 'Show';
  }
}

function copyIspInfo() {
  const text = `ISP: ${document.getElementById('ispName').innerText}\nIP: ${document.getElementById('ispPublic').innerText}\nLocal IP: ${document.getElementById('ispIPv4').innerText}\nGateway: ${document.getElementById('ispGw').innerText}`;
  navigator.clipboard.writeText(text);
  log("ISP Network Information copied to clipboard.");
}

// ==========================================
// QUICK ACTIONS & UPDATES
// ==========================================
async function triggerUpdateCheck() {
  const btn = document.getElementById('updateSyncBtn');
  const statusEl = document.getElementById('updateStatusText');
  
  btn.classList.add('spinning');
  statusEl.innerHTML = "Checking for updates...";
  
  await new Promise(r => setTimeout(r, 1500));
  
  const res = await pywebview.api.check_updates();
  if (res.update_available) {
    statusEl.innerHTML = `Current: ${CURRENT_VERSION} <br><strong>New Release: ${res.latest_version} ready.</strong>`;
    document.getElementById('btnUpdate').style.display = 'inline-block';
  } else {
    statusEl.innerHTML = `Current Version: ${CURRENT_VERSION} <br><span style="color: #4ade80; font-size: 0.85rem;">App is fully up-to-date.</span>`;
  }
  btn.classList.remove('spinning');
}

function triggerUpdate() { log("Applying update..."); pywebview.api.apply_update(); }

async function runRefresh() {
  log("Refreshing network adapters...");
  const res = await pywebview.api.quick_refresh();
  log(res.message);
}

async function runDeepRepair() {
  log("Executing Deep TCP/IP & Winsock resets...");
  const res = await pywebview.api.deep_repair();
  log(res.message);
}

async function checkCurrentDns() {
  log("Querying OS network adapters...");
  const res = await pywebview.api.get_current_dns();
  log(res.message);
}

// ==========================================
// DNS SWITCHER LOGIC
// ==========================================
async function applyDnsVisuals(actionPromise, profileName) {
  const visualizer = document.getElementById('dnsVisualizer');
  const visText = document.getElementById('dnsVisualText');
  const pulse = document.getElementById('dnsPulse');
  
  visualizer.classList.add('active');
  visText.textContent = `Applying ${profileName} profile...`;
  
  const res = await actionPromise;
  
  if (res.status === 'success') {
    visText.textContent = `Success: ${profileName} applied.`;
    log(res.message);
  } else {
    visualizer.style.borderColor = 'var(--danger)';
    visualizer.style.color = 'var(--danger)';
    pulse.style.background = 'var(--danger)';
    visText.textContent = "Error: Admin Rights Required";
    log(`[ERROR] ${res.message}`);
  }
  
  setTimeout(() => {
    visualizer.classList.remove('active');
    visualizer.style.borderColor = ''; visualizer.style.color = ''; pulse.style.background = '';
    visText.textContent = "DNS Engine Ready";
  }, 4000);
}

function setDnsProfile(profile) {
  log(`Setting predefined DNS: ${profile}...`);
  let promise;
  if (profile === 'cache') promise = pywebview.api.set_dns('10.11.12.13', '8.8.8.8');
  else if (profile === 'raw') promise = pywebview.api.set_dns('1.1.1.1', '8.8.8.8');
  else promise = pywebview.api.set_dns('dhcp');
  applyDnsVisuals(promise, profile.toUpperCase());
}

function applyCustomDns() {
  const p = document.getElementById('customPrimary').value.trim();
  const s = document.getElementById('customSecondary').value.trim();
  if (!p) return log("[ERROR] Primary DNS required.");
  log(`Applying Custom DNS: ${p}`);
  applyDnsVisuals(pywebview.api.set_dns(p, s || null), "CUSTOM");
}

// ==========================================
// ADVANCED ROUTING (PING & SORT)
// ==========================================
let currentPingResults = [];
let pingSortState = 0; 

async function runPingCheck() {
  log("Tracing dynamic gateways and executing routing telemetry...");
  document.getElementById('pingTableBody').innerHTML = `<tr><td colspan="4">Tracing route to ISP... please wait.</td></tr>`;
  
  currentPingResults = await pywebview.api.run_ping_diagnostics();
  pingSortState = 0; 
  renderPingTable();
  log("Telemetry sweep completed.");
}

function togglePingSort() {
  if(currentPingResults.length === 0) return;
  pingSortState = (pingSortState + 1) % 3;
  
  if(pingSortState === 0) {
    log("Ping table restored to default order.");
  } else {
    currentPingResults.sort((a, b) => {
      let valA = a.latency === "Timeout" ? 9999 : parseInt(a.latency) || 0;
      let valB = b.latency === "Timeout" ? 9999 : parseInt(b.latency) || 0;
      return pingSortState === 1 ? valA - valB : valB - valA;
    });
    log(pingSortState === 1 ? "Ping table sorted: Best to Worst." : "Ping table sorted: Worst to Best.");
  }
  renderPingTable();
}

async function renderPingTable() {
  const tbody = document.getElementById('pingTableBody');
  tbody.innerHTML = "";
  for (const r of currentPingResults) {
    const color = r.packet_loss === '0%' ? '#4ade80' : (r.packet_loss === 'N/A' ? '#64748b' : '#ef4444');
    tbody.innerHTML += `<tr>
      <td>${r.name}</td><td>${r.ip}</td>
      <td><strong>${r.latency}</strong></td>
      <td><span style="color: ${color}">${r.packet_loss}</span></td>
    </tr>`;
    if(pingSortState === 0 && r.latency !== "N/A") { 
      await savePingHistory(r.name, r.latency, r.packet_loss); 
    }
  }
}

// ==========================================
// BANDWIDTH MEASUREMENT (FIXED SERVERS)
// ==========================================
async function runSpeedtest(target) {
  const isSg = target === 'singapore';
  const display = document.getElementById(isSg ? 'sgOutput' : 'bdixOutput');
  const targetText = document.getElementById(isSg ? 'sgTargetText' : 'bdixTargetText');
  const typeName = isSg ? "RAW Speed" : "BDIX Speed";
  
  display.textContent = "Testing...";

  if (!isSg) {
      targetText.textContent = "Target: Auto-selecting local BDIX node (Queued...)";
      log(`Initializing BDIX bandwidth test protocol...`);
      
      const res = await pywebview.api.run_speedtest("bdix"); 
      
      if (res.status === 'success') {
          display.textContent = `${res.download_mbps} Mbps`;
          targetText.textContent = `Target: ${res.server}`; 
          log(`BDIX Result [${res.server.split(' ')[0]}]: ${res.download_mbps} Mbps Down | ${res.upload_mbps} Mbps Up`);
          saveSpeedHistory(typeName, `${res.download_mbps} Mbps`, `${res.upload_mbps} Mbps`, res.ping_ms);
      } else {
          display.textContent = "Error";
          targetText.textContent = "Target: Test Failed";
          log(`BDIX Error: ${res.message}`);
      }
  } else {
      targetText.textContent = "Target: Singtel Singapore (Queued...)";
      log(`Initializing RAW bandwidth test on Singtel...`);
      
      const res = await pywebview.api.run_speedtest("singapore");
      
      if(res.status === 'success') {
          display.textContent = `${res.download_mbps} Mbps`;
          targetText.textContent = `Target: ${res.server}`; 
          log(`RAW Result [Singtel]: ${res.download_mbps} Mbps Down | ${res.upload_mbps} Mbps Up`);
          saveSpeedHistory(typeName, `${res.download_mbps} Mbps`, `${res.upload_mbps} Mbps`, res.ping_ms);
      } else {
          display.textContent = "Error";
          targetText.textContent = "Target: Test Failed";
          log(`RAW Error: ${res.message}`);
      }
  }
}

// ==========================================
// HISTORY MANAGEMENT
// ==========================================
async function loadHistory() {
  const history = await pywebview.api.load_history();
  
  const sBody = document.getElementById('speedHistoryTableBody');
  sBody.innerHTML = history.speed.length ? '' : '<tr><td colspan="5">No data available.</td></tr>';
  [...history.speed].reverse().forEach(e => {
    sBody.innerHTML += `<tr><td>${e.date}</td><td><strong>${e.type}</strong></td><td style="color:#38bdf8;">${e.down}</td><td>${e.up}</td><td>${e.ping} ms</td></tr>`;
  });

  const pBody = document.getElementById('pingHistoryTableBody');
  pBody.innerHTML = history.ping.length ? '' : '<tr><td colspan="4">No data available.</td></tr>';
  [...history.ping].reverse().forEach(e => {
    pBody.innerHTML += `<tr><td>${e.date}</td><td><strong>${e.target}</strong></td><td>${e.latency}</td><td>${e.loss}</td></tr>`;
  });
}

async function saveSpeedHistory(type, down, up, ping) {
  const h = await pywebview.api.load_history();
  h.speed.push({ date: new Date().toLocaleString(), type, down, up, ping });
  await pywebview.api.save_history(h);
  loadHistory();
}

async function savePingHistory(target, latency, loss) {
  const h = await pywebview.api.load_history();
  h.ping.push({ date: new Date().toLocaleTimeString(), target, latency, loss });
  await pywebview.api.save_history(h);
  loadHistory();
}

async function clearHistory() {
  if(confirm("Permanently wipe all diagnostic records?")) {
    await pywebview.api.clear_history();
    loadHistory();
    log("Diagnostic storage formatted successfully.");
  }
}