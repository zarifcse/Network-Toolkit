const CURRENT_VERSION = "v1.0.0";

function switchTab(tabName) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
  document.getElementById(`tab-${tabName}`).classList.add('active');
  if (event && event.currentTarget) { event.currentTarget.classList.add('active'); }
}

function log(msg) {
  const terminal = document.getElementById('statusConsole');
  terminal.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
}

let pendingUpdateUrl = null;

window.addEventListener('pywebviewready', async () => {
  log("Connected to Python backend runtime.");
  triggerUpdateCheck();
  loadHistory(); 
});

async function triggerUpdateCheck() {
  const btn = document.getElementById('updateSyncBtn');
  const statusEl = document.getElementById('updateStatusText');
  
  btn.classList.add('spinning'); // Start animation
  statusEl.textContent = "Checking GitHub...";
  
  const res = await pywebview.api.check_updates();
  
  if (res.update_available) {
    statusEl.innerHTML = `Current: ${CURRENT_VERSION} <br><strong>New Release: ${res.latest_version} ready.</strong>`;
    pendingUpdateUrl = res.download_url;
    document.getElementById('btnUpdate').style.display = 'inline-block';
  } else {
    statusEl.innerHTML = `Current Version: ${CURRENT_VERSION} <br><span style="color: #4ade80; font-size: 0.85rem;">App is fully up-to-date.</span>`;
  }
  
  btn.classList.remove('spinning'); // Stop animation
}

async function runRefresh() {
  log("Refreshing network configuration...");
  const res = await pywebview.api.quick_refresh();
  log(res.message);
}

async function runDeepRepair() {
  log("Running deep TCP/IP Winsock resets...");
  const res = await pywebview.api.deep_repair();
  log(res.message);
}

async function checkCurrentDns() {
  log("Querying active DNS configurations...");
  const res = await pywebview.api.get_current_dns();
  log(res.message);
}

async function setDnsProfile(profile) {
  const visualizer = document.getElementById('dnsVisualizer');
  const visText = document.getElementById('dnsVisualText');
  const pulse = document.getElementById('dnsPulse');
  
  visualizer.classList.add('active');
  visText.textContent = `Applying ${profile.toUpperCase()} profile...`;
  log(`Applying ${profile} DNS settings...`);
  
  let res;
  if (profile === 'cache') res = await pywebview.api.set_dns('10.11.12.13', '8.8.8.8');
  else if (profile === 'raw') res = await pywebview.api.set_dns('1.1.1.1', '8.8.8.8');
  else res = await pywebview.api.set_dns('dhcp');
  
  // VERIFY BACKEND SUCCESS
  if (res.status === 'success') {
    visText.textContent = `Success: ${profile.toUpperCase()} applied.`;
    log(res.message);
  } else {
    // Show error visually in the UI
    visualizer.style.borderColor = 'var(--danger)';
    visualizer.style.color = 'var(--danger)';
    pulse.style.background = 'var(--danger)';
    pulse.style.boxShadow = '0 0 8px var(--danger)';
    visText.textContent = "Error: Admin Rights Required";
    log(`[ERROR] ${res.message}`);
  }
  
  setTimeout(() => {
    visualizer.classList.remove('active');
    // Reset any error colors
    visualizer.style.borderColor = '';
    visualizer.style.color = '';
    pulse.style.background = '';
    pulse.style.boxShadow = '';
    visText.textContent = "DNS Engine Ready";
  }, 4000);
}

// ==========================================
// HISTORY MANAGEMENT (SPLIT TABLES)
// ==========================================
function loadHistory() {
  const speedHistory = JSON.parse(localStorage.getItem('speedTestHistory') || '[]');
  const sBody = document.getElementById('speedHistoryTableBody');
  sBody.innerHTML = '';
  if(speedHistory.length === 0) {
    sBody.innerHTML = '<tr><td colspan="5">No speed tests recorded yet.</td></tr>';
  } else {
    [...speedHistory].reverse().forEach(entry => {
      sBody.innerHTML += `<tr>
        <td>${entry.date}</td>
        <td><strong>${entry.type}</strong></td>
        <td style="color: #38bdf8;">${entry.down}</td>
        <td>${entry.up}</td>
        <td>${entry.ping} ms</td>
      </tr>`;
    });
  }

  const pingHistory = JSON.parse(localStorage.getItem('pingTestHistory') || '[]');
  const pBody = document.getElementById('pingHistoryTableBody');
  pBody.innerHTML = '';
  if(pingHistory.length === 0) {
    pBody.innerHTML = '<tr><td colspan="4">No ping tests recorded yet.</td></tr>';
  } else {
    [...pingHistory].reverse().forEach(entry => {
      pBody.innerHTML += `<tr>
        <td>${entry.date}</td>
        <td><strong>${entry.target}</strong></td>
        <td>${entry.latency}</td>
        <td><span style="color: ${entry.loss === '0%' ? '#4ade80' : '#ef4444'}">${entry.loss}</span></td>
      </tr>`;
    });
  }
}

function saveSpeedHistory(type, down, up, ping) {
  const history = JSON.parse(localStorage.getItem('speedTestHistory') || '[]');
  const date = new Date().toLocaleString();
  history.push({ date, type, down, up, ping });
  // TRUNCATION REMOVED: Will now save forever
  localStorage.setItem('speedTestHistory', JSON.stringify(history));
  loadHistory();
}

function savePingHistory(target, latency, loss) {
  const history = JSON.parse(localStorage.getItem('pingTestHistory') || '[]');
  const date = new Date().toLocaleTimeString(); 
  history.push({ date, target, latency, loss });
  // TRUNCATION REMOVED: Will now save forever
  localStorage.setItem('pingTestHistory', JSON.stringify(history));
  loadHistory();
}

// NEW FUNCTION: Wipes all saved history
function clearHistory() {
  // Triggers a native Windows confirmation popup
  if(confirm("Are you sure you want to delete all diagnostic history? This cannot be undone.")) {
    localStorage.removeItem('speedTestHistory');
    localStorage.removeItem('pingTestHistory');
    loadHistory();
    log("Diagnostic history cleared successfully.");
  }
}

// ==========================================
// DIAGNOSTICS EXECUTION
// ==========================================
async function runPingCheck() {
  log("Executing ping telemetry across game and DNS clusters...");
  const tbody = document.getElementById('pingTableBody');
  tbody.innerHTML = `<tr><td colspan="4">Testing targets... please wait.</td></tr>`;
  
  const results = await pywebview.api.run_ping_diagnostics();
  tbody.innerHTML = "";
  
  results.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.name}</td>
      <td>${r.ip}</td>
      <td><strong>${r.latency}</strong></td>
      <td><span style="color: ${r.packet_loss === '0%' ? '#4ade80' : '#ef4444'}">${r.packet_loss}</span></td>
    `;
    tbody.appendChild(tr);
    savePingHistory(r.name, r.latency, r.packet_loss);
  });
  log("Diagnostics completed.");
}

async function runSpeedtest(target) {
  const isSg = target === 'singapore';
  const display = document.getElementById(isSg ? 'sgOutput' : 'bdixOutput');
  const typeName = isSg ? "RAW Speed" : "BDIX Speed";
  
  display.textContent = "Testing...";
  log(`Running bandwidth measurement (${target.toUpperCase()})...`);

  const res = await pywebview.api.run_speedtest(isSg ? "13623" : null);
  if (res.status === 'success') {
    display.textContent = `${res.download_mbps} Mbps`;
    
    // NEW LOGIC: Inject the specific server name into the UI for BDIX
    if (!isSg) {
      document.getElementById('bdixTargetText').textContent = `Target: ${res.server}`;
    }

    log(`Finished: ${res.download_mbps} Mbps Down / ${res.upload_mbps} Mbps Up (${res.ping_ms} ms)`);
    saveSpeedHistory(typeName, `${res.download_mbps} Mbps`, `${res.upload_mbps} Mbps`, res.ping_ms);
  } else {
    display.textContent = "Error";
    log(res.message);
  }
}

function triggerUpdate() {
  if (pendingUpdateUrl) {
    log("Downloading update and restarting...");
    pywebview.api.apply_update(pendingUpdateUrl);
  }
}