function switchTab(tabName) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
  document.getElementById(`tab-${tabName}`).classList.add('active');
  
  // Handle event object safely depending on how it's called
  if (event && event.currentTarget) {
      event.currentTarget.classList.add('active');
  }
}

function log(msg) {
  const terminal = document.getElementById('statusConsole');
  terminal.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
}

let pendingUpdateUrl = null;

// This triggers as soon as the Python backend is fully connected to the UI
window.addEventListener('pywebviewready', async () => {
  log("Connected to Python backend runtime.");
  
  // Check GitHub for updates silently in the background
  const res = await pywebview.api.check_updates();
  const statusEl = document.getElementById('updateStatusText');
  if (res.update_available) {
    statusEl.innerHTML = `New release <strong>${res.latest_version}</strong> ready.`;
    pendingUpdateUrl = res.download_url;
    document.getElementById('btnUpdate').style.display = 'inline-block';
  } else {
    statusEl.textContent = "Application is up-to-date.";
  }
});

async function runRefresh() {
  log("Refreshing network configuration...");
  const res = await pywebview.api.quick_refresh();
  log(res.message);
}

async function runDeepRepair() {
  log("Running deep TCP/IP Winsock resets (Admin elevation required)...");
  const res = await pywebview.api.deep_repair();
  log(res.message);
}

async function setDnsProfile(profile) {
  log(`Applying ${profile} DNS settings...`);
  let res;
  if (profile === 'cache') res = await pywebview.api.set_dns('10.11.12.13', '8.8.8.8');
  else if (profile === 'raw') res = await pywebview.api.set_dns('1.1.1.1', '8.8.8.8');
  else res = await pywebview.api.set_dns('dhcp');
  log(res.message);
}

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
  });
  log("Diagnostics completed.");
}

async function runSpeedtest(target) {
  const isSg = target === 'singapore';
  const display = document.getElementById(isSg ? 'sgOutput' : 'bdixOutput');
  display.textContent = "Testing...";
  log(`Running bandwidth measurement (${target.toUpperCase()})...`);

  const res = await pywebview.api.run_speedtest(isSg ? "13623" : null);
  if (res.status === 'success') {
    display.textContent = `${res.download_mbps} Mbps`;
    log(`Finished: ${res.download_mbps} Mbps Down / ${res.upload_mbps} Mbps Up (${res.ping_ms} ms)`);
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