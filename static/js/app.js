
// NVIDIA GPU Benchmark Tool - Frontend

const socket = io();
let gpuData = [];
let activeBenchmarks = {};
let chartHistory = { labels: [], temp: {}, util: {}, fan: {}, power: {} };
const MAX_HISTORY = 120;
let charts = {};

// Log stores
const logStores = { system: [], temperature: [], fan: [], warnings: [], benchmark: [] };

// Auto fan curve state
let autoFanStatus = {};

// DOM refs
const connectionStatus = document.getElementById('connection-status');
const connectionText = document.getElementById('connection-text');
const gpuCount = document.getElementById('gpu-count');
const currentTime = document.getElementById('current-time');
const gpuSelector = document.getElementById('gpu-selector');
const gpusContainer = document.getElementById('gpus-container');
const activeBenchmarksDiv = document.getElementById('active-benchmarks');
const stressLevel = document.getElementById('stress-level');
const stressValue = document.getElementById('stress-value');
const memoryLevel = document.getElementById('memory-level');
const memoryValue = document.getElementById('memory-value');
const powerLimitSlider = document.getElementById('power-limit');
const powerLimitValue = document.getElementById('power-limit-value');

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    setupTabs();
    setupLogTabs();
    updateTime();
    setInterval(updateTime, 1000);
    initCharts();
});

// ===== TABS =====
function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('tab-' + tab).classList.add('active');
            if (tab === 'system') loadSystemInfo();
            if (tab === 'results') loadResults();
        });
    });
}

function setupLogTabs() {
    document.querySelectorAll('.log-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const ltab = btn.dataset.logtab;
            document.querySelectorAll('.log-tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.log-tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('logtab-' + ltab).classList.add('active');
        });
    });
}

// ===== SOCKET.IO =====
socket.on('connect', () => {
    connectionStatus.classList.add('connected');
    connectionText.textContent = 'Connected';
    addLog('system', 'info', 'Connected to server');
    socket.emit('start_monitoring');
    loadFanAutoStatus();
});

socket.on('disconnect', () => {
    connectionStatus.classList.remove('connected');
    connectionText.textContent = 'Disconnected';
    addLog('system', 'error', 'Disconnected from server');
});

socket.on('gpu_update', (data) => {
    gpuData = data.gpus || [];
    activeBenchmarks = data.benchmarks || {};
    updateGPUDisplay();
    updateActiveBenchmarks();
    gpuCount.textContent = gpuData.length;
    recordHistory(data);
});

socket.on('monitoring_status', (data) => {
    addLog('system', 'info', data.active ? 'Monitoring started' : 'Monitoring stopped');
});

// ===== HISTORY & CHARTS =====
function recordHistory(data) {
    const now = new Date().toLocaleTimeString();
    chartHistory.labels.push(now);
    if (chartHistory.labels.length > MAX_HISTORY) chartHistory.labels.shift();

    const gpus = data.gpus || [];
    gpus.forEach(gpu => {
        const i = gpu.index;
        ['temp', 'util', 'fan', 'power'].forEach(k => {
            if (!chartHistory[k][i]) chartHistory[k][i] = [];
        });
        const temp = gpu.temperature;
        const util = gpu.utilization.gpu;
        const fan = gpu.fan_speed;
        const power = gpu.power.usage;

        chartHistory.temp[i].push(temp);
        chartHistory.util[i].push(util);
        chartHistory.fan[i].push(fan);
        chartHistory.power[i].push(power);

        if (chartHistory.temp[i].length > MAX_HISTORY) {
            chartHistory.temp[i].shift();
            chartHistory.util[i].shift();
            chartHistory.fan[i].shift();
            chartHistory.power[i].shift();
        }

        // Log temperature row every 5s (every 5 updates)
        if (chartHistory.labels.length % 5 === 0) {
            addTempLog(gpu);
            addFanLog(gpu);
        }

        // Warnings
        const maxTemp = parseInt(document.getElementById('max-temp').value) || 100;
        const critTemp = parseInt(document.getElementById('critical-temp').value) || 105;
        if (temp >= critTemp) {
            addWarningLog(i, 'CRITICAL TEMP', `GPU ${i} temperature ${temp}°C exceeds critical limit ${critTemp}°C`);
        } else if (temp >= maxTemp) {
            addWarningLog(i, 'HIGH TEMP', `GPU ${i} temperature ${temp}°C exceeds max ${maxTemp}°C`);
        }
    });
    updateCharts();
}

const GPU_COLORS = ['#76b900','#2196F3','#FF5722','#9C27B0','#00BCD4'];

function initCharts() {
    const chartDefs = [
        { id: 'chart-temperature', label: 'Temperature (°C)', dataKey: 'temp', yLabel: '°C', suggestedMax: 110 },
        { id: 'chart-power', label: 'Power (W)', dataKey: 'power', yLabel: 'W', suggestedMax: 400 },
        { id: 'chart-fan', label: 'Fan Speed (%)', dataKey: 'fan', yLabel: '%', suggestedMax: 100 },
        { id: 'chart-utilization', label: 'GPU Utilization (%)', dataKey: 'util', yLabel: '%', suggestedMax: 100 },
    ];
    chartDefs.forEach(def => {
        const canvas = document.getElementById(def.id);
        if (!canvas) return;
        charts[def.id] = { chart: null, def };
    });
}

function getOrCreateChart(chartId) {
    const entry = charts[chartId];
    if (!entry) return null;
    if (entry.chart) return entry.chart;

    const canvas = document.getElementById(chartId);
    if (!canvas) return null;
    const def = entry.def;

    const datasets = [];
    Object.keys(chartHistory[def.dataKey]).forEach((gpuIdx, i) => {
        datasets.push({
            label: `GPU ${gpuIdx}`,
            data: chartHistory[def.dataKey][gpuIdx],
            borderColor: GPU_COLORS[i % GPU_COLORS.length],
            backgroundColor: 'transparent',
            tension: 0.3,
            pointRadius: 0,
            borderWidth: 2,
        });
    });

    entry.chart = new Chart(canvas, {
        type: 'line',
        data: { labels: chartHistory.labels, datasets },
        options: {
            responsive: true,
            animation: false,
            plugins: {
                legend: { labels: { color: '#888', boxWidth: 12 } },
                title: { display: true, text: def.label, color: '#76b900', font: { size: 13 } },
            },
            scales: {
                x: { ticks: { color: '#666', maxTicksLimit: 8 }, grid: { color: '#222' } },
                y: { ticks: { color: '#888' }, grid: { color: '#222' }, suggestedMax: def.suggestedMax, min: 0, title: { display: true, text: def.yLabel, color: '#888' } },
            },
        }
    });
    return entry.chart;
}

function updateCharts() {
    Object.keys(charts).forEach(chartId => {
        const entry = charts[chartId];
        if (!entry.chart) {
            getOrCreateChart(chartId);
            return;
        }
        const def = entry.def;
        const chart = entry.chart;

        chart.data.labels = [...chartHistory.labels];

        // Update or add datasets per GPU
        const gpuKeys = Object.keys(chartHistory[def.dataKey]);
        gpuKeys.forEach((gpuIdx, i) => {
            if (chart.data.datasets[i]) {
                chart.data.datasets[i].data = [...chartHistory[def.dataKey][gpuIdx]];
            } else {
                chart.data.datasets.push({
                    label: `GPU ${gpuIdx}`,
                    data: [...chartHistory[def.dataKey][gpuIdx]],
                    borderColor: GPU_COLORS[i % GPU_COLORS.length],
                    backgroundColor: 'transparent',
                    tension: 0.3, pointRadius: 0, borderWidth: 2,
                });
            }
        });
        chart.update('none');
    });
}

// ===== LOG FUNCTIONS =====
function addLog(category, level, message) {
    const ts = new Date().toLocaleTimeString();
    const entry = { ts, level, message };
    logStores[category] = logStores[category] || [];
    logStores[category].push(entry);
    if (logStores[category].length > 500) logStores[category].shift();

    // Render to table
    const tbody = document.getElementById('log-table-' + category);
    if (!tbody) return;

    // Remove placeholder
    const placeholder = tbody.querySelector('.no-data-cell');
    if (placeholder) placeholder.parentElement.remove();

    const tr = document.createElement('tr');
    const lvlClass = { info: 'log-level-info', warning: 'log-level-warn', error: 'log-level-error', critical: 'log-level-critical' }[level] || 'log-level-info';
    tr.innerHTML = `<td>${ts}</td><td><span class="${lvlClass}">${level.toUpperCase()}</span></td><td>${escHtml(message)}</td>`;
    tbody.insertBefore(tr, tbody.firstChild);
    while (tbody.rows.length > 200) tbody.deleteRow(tbody.rows.length - 1);
}

function addTempLog(gpu) {
    const ts = new Date().toLocaleTimeString();
    const tbody = document.getElementById('log-table-temperature');
    if (!tbody) return;
    const placeholder = tbody.querySelector('.no-data-cell');
    if (placeholder) placeholder.parentElement.remove();
    const tempClass = gpu.temperature >= 100 ? 'style="color:#ff5252"' : gpu.temperature >= 85 ? 'style="color:#ffc107"' : '';
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${ts}</td><td>GPU ${gpu.index}</td><td ${tempClass}>${gpu.temperature}°C</td><td>${gpu.utilization.gpu}%</td><td>${gpu.power.usage.toFixed(1)} W</td><td>${gpu.clocks.graphics} MHz</td>`;
    tbody.insertBefore(tr, tbody.firstChild);
    while (tbody.rows.length > 300) tbody.deleteRow(tbody.rows.length - 1);
}

function addFanLog(gpu) {
    const ts = new Date().toLocaleTimeString();
    const tbody = document.getElementById('log-table-fan');
    if (!tbody) return;
    const placeholder = tbody.querySelector('.no-data-cell');
    if (placeholder) placeholder.parentElement.remove();
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${ts}</td><td>GPU ${gpu.index}</td><td>${gpu.fan_speed}%</td><td>${gpu.temperature}°C</td><td>${gpu.power.usage.toFixed(1)} W</td>`;
    tbody.insertBefore(tr, tbody.firstChild);
    while (tbody.rows.length > 300) tbody.deleteRow(tbody.rows.length - 1);
}

let warnCooldown = {};
function addWarningLog(gpuIdx, type, detail) {
    const key = `${gpuIdx}_${type}`;
    const now = Date.now();
    if (warnCooldown[key] && now - warnCooldown[key] < 10000) return;
    warnCooldown[key] = now;

    const ts = new Date().toLocaleTimeString();
    const tbody = document.getElementById('log-table-warnings');
    if (!tbody) return;
    const placeholder = tbody.querySelector('.no-data-cell');
    if (placeholder) placeholder.parentElement.remove();
    const colorMap = { 'CRITICAL TEMP': '#ff5252', 'HIGH TEMP': '#ffc107' };
    const color = colorMap[type] || '#888';
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${ts}</td><td>GPU ${gpuIdx}</td><td style="color:${color};font-weight:700">${type}</td><td>${escHtml(detail)}</td>`;
    tbody.insertBefore(tr, tbody.firstChild);
    while (tbody.rows.length > 200) tbody.deleteRow(tbody.rows.length - 1);
}

function addBenchmarkLog(level, message) {
    addLog('benchmark', level, message);
    addLog('system', level, message);
}

function escHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function clearLogs() {
    Object.keys(logStores).forEach(k => { logStores[k] = []; });
    ['system','temperature','fan','warnings','benchmark'].forEach(k => {
        const tbody = document.getElementById('log-table-' + k);
        if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="no-data-cell">Cleared</td></tr>`;
    });
    chartHistory = { labels: [], temp: {}, util: {}, fan: {}, power: {} };
    Object.values(charts).forEach(e => { if (e.chart) { e.chart.destroy(); e.chart = null; } });
    addLog('system', 'info', 'Logs cleared');
}

function exportLogs() {
    const data = JSON.stringify({ exported: new Date().toISOString(), logs: logStores }, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gpu-logs-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// ===== GPU DISPLAY =====
function setupEventListeners() {
    stressLevel.addEventListener('input', e => { stressValue.textContent = e.target.value + '%'; });
    memoryLevel.addEventListener('input', e => { memoryValue.textContent = e.target.value + '%'; });
    powerLimitSlider.addEventListener('input', e => { powerLimitValue.textContent = e.target.value + ' W'; });
    document.getElementById('start-benchmark').addEventListener('click', startBenchmark);
    document.getElementById('stop-all-benchmarks').addEventListener('click', stopAllBenchmarks);
    document.getElementById('save-config').addEventListener('click', saveConfiguration);
}

function updateTime() {
    currentTime.textContent = new Date().toLocaleTimeString();
}

function updateGPUDisplay() {
    if (gpuData.length === 0) {
        gpusContainer.innerHTML = '<p class="no-data">No GPUs detected.</p>';
        gpuSelector.innerHTML = '<p class="no-data">No GPUs available</p>';
        return;
    }
    if (gpuSelector.children.length === 0) {
        gpuData.forEach(gpu => {
            const label = document.createElement('label');
            label.className = 'gpu-checkbox';
            label.innerHTML = `<input type="checkbox" value="${gpu.index}" checked> <span>GPU ${gpu.index}: ${gpu.name}</span>`;
            gpuSelector.appendChild(label);
        });
    }
    gpusContainer.innerHTML = '';
    gpuData.forEach(gpu => gpusContainer.appendChild(createGPUCard(gpu)));
    renderFanControls();
    // Update live fan speed displays in fan control panel
    gpuData.forEach(gpu => {
        const el = document.getElementById(`fan-speed-live-${gpu.index}`);
        if (el) el.textContent = gpu.fan_speed + '%';
        const sl = document.getElementById(`fan-slider-${gpu.index}`);
        // Only update slider if user isn't actively dragging (no focus)
        if (sl && document.activeElement !== sl) sl.value = gpu.fan_speed;
        const sv = document.getElementById(`fan-slider-val-${gpu.index}`);
        if (sv && document.activeElement !== document.getElementById(`fan-slider-${gpu.index}`)) sv.textContent = gpu.fan_speed + '%';
    });
}

function renderFanControls() {
    const container = document.getElementById('fan-controls-container');
    if (!container) return;
    // Only build the cards once (avoid destroying slider while user drags)
    if (container.querySelector('.fan-gpu-card')) return;
    container.innerHTML = '';
    gpuData.forEach(gpu => {
        const isAuto = autoFanStatus[gpu.index] || false;
        const card = document.createElement('div');
        card.className = 'fan-gpu-card';
        card.id = `fan-card-${gpu.index}`;
        card.innerHTML = `
            <div class="fan-gpu-header">
                <strong>GPU ${gpu.index}: ${gpu.name}</strong>
                <span class="fan-speed-badge">🌀 <span id="fan-speed-live-${gpu.index}">${gpu.fan_speed}</span>%</span>
            </div>
            <div class="fan-mode-row">
                <button id="fan-auto-btn-${gpu.index}"
                    class="btn ${isAuto ? 'btn-primary' : 'btn-secondary'}"
                    onclick="toggleAutoFan(${gpu.index})"
                    style="font-size:12px;padding:5px 14px">
                    ${isAuto ? '🟢 Auto Curve ON' : '⬜ Auto Curve OFF'}
                </button>
                <span style="font-size:11px;color:var(--text2);margin-left:10px">
                    ${isAuto ? 'Adjusting fan by temperature automatically' : 'Click to enable temperature tracking'}
                </span>
            </div>
            <div class="fan-manual-row" id="fan-manual-${gpu.index}" style="${isAuto ? 'opacity:0.45;pointer-events:none' : ''}">
                <label style="font-size:12px;color:var(--text2)">Manual fixed speed:</label>
                <div style="display:flex;align-items:center;gap:8px;margin-top:5px">
                    <input type="range" id="fan-slider-${gpu.index}" min="0" max="100" value="${gpu.fan_speed}" step="5"
                        style="flex:1"
                        oninput="document.getElementById('fan-slider-val-${gpu.index}').textContent=this.value+'%'">
                    <span id="fan-slider-val-${gpu.index}" style="font-size:13px;font-weight:700;min-width:40px;color:var(--primary)">${gpu.fan_speed}%</span>
                    <button class="btn btn-secondary" style="font-size:12px;padding:4px 12px"
                        onclick="applyManualFan(${gpu.index})">Apply</button>
                    <button class="btn btn-secondary" style="font-size:12px;padding:4px 12px"
                        onclick="resetFanControl(${gpu.index})">↺ Reset Auto</button>
                </div>
            </div>`;
        container.appendChild(card);
    });
}

function createGPUCard(gpu) {
    const card = document.createElement('div');
    card.className = 'gpu-card';
    if (gpu.temperature >= 105) card.classList.add('critical');
    else if (gpu.temperature >= 90) card.classList.add('hot');

    const tC = gpu.temperature >= 105 ? 'danger' : gpu.temperature >= 90 ? 'warning' : '';
    const uC = gpu.utilization.gpu >= 90 ? 'warning' : '';
    const mC = gpu.memory.percent >= 90 ? 'warning' : '';

    card.innerHTML = `
        <div class="gpu-header">
            <div class="gpu-name">${gpu.name}</div>
            <div class="gpu-index">GPU ${gpu.index}</div>
        </div>
        <div class="gpu-stats">
            <div class="stat-item">
                <div class="stat-label">🌡️ Temperature</div>
                <div class="stat-value ${tC}">${gpu.temperature}°C</div>
                <div class="progress-bar"><div class="progress-fill ${tC}" style="width:${Math.min(gpu.temperature,110)/110*100}%"></div></div>
            </div>
            <div class="stat-item">
                <div class="stat-label">⚡ GPU Util</div>
                <div class="stat-value ${uC}">${gpu.utilization.gpu}%</div>
                <div class="progress-bar"><div class="progress-fill ${uC}" style="width:${gpu.utilization.gpu}%"></div></div>
            </div>
            <div class="stat-item">
                <div class="stat-label">💾 Memory</div>
                <div class="stat-value ${mC}">${gpu.memory.used_mb.toFixed(0)} MB</div>
                <div class="progress-bar"><div class="progress-fill ${mC}" style="width:${gpu.memory.percent}%"></div></div>
            </div>
            <div class="stat-item">
                <div class="stat-label">🔋 Power</div>
                <div class="stat-value">${gpu.power.usage.toFixed(1)} / ${gpu.power.limit.toFixed(0)} W</div>
                <div class="progress-bar"><div class="progress-fill" style="width:${gpu.power.percent}%"></div></div>
            </div>
            <div class="stat-item">
                <div class="stat-label">🌀 Fan</div>
                <div class="stat-value">${gpu.fan_speed}%</div>
                <div class="progress-bar"><div class="progress-fill" style="width:${gpu.fan_speed}%"></div></div>
            </div>
            <div class="stat-item">
                <div class="stat-label">⚙️ Clock</div>
                <div class="stat-value">${gpu.clocks.graphics} MHz</div>
            </div>
        </div>`;
    return card;
}

function updateActiveBenchmarks() {
    const keys = Object.keys(activeBenchmarks);
    if (keys.length === 0) {
        activeBenchmarksDiv.innerHTML = '<p class="no-data">No active benchmarks</p>';
        return;
    }
    activeBenchmarksDiv.innerHTML = '';
    keys.forEach(id => {
        const b = activeBenchmarks[id];
        const elapsed = parseFloat(b.elapsed).toFixed(0);
        const remaining = Math.max(0, b.duration - elapsed);
        const pct = Math.min(100, (elapsed / b.duration * 100)).toFixed(1);
        let statusClass = 'running', statusText = b.status;
        if (b.status === 'stopped_critical_temp') { statusClass = 'critical'; statusText = 'STOPPED - Critical Temp'; }
        else if (b.status === 'completed') { statusClass = 'completed'; statusText = 'Completed'; }
        else if (b.status === 'error') { statusClass = 'error'; statusText = 'Error'; }

        const item = document.createElement('div');
        item.className = 'benchmark-item';
        item.innerHTML = `
            <div class="benchmark-header">
                <div class="benchmark-id">${id}</div>
                <div class="benchmark-status ${statusClass}">${statusText}</div>
                ${b.status === 'running' ? `<button class="btn btn-danger" style="padding:4px 10px;font-size:12px" onclick="stopBenchmark('${id}')">Stop</button>` : ''}
            </div>
            <div class="benchmark-info">
                <div>📊 GPUs: ${b.gpu_indices.join(', ')}</div>
                <div>⚡ Stress: ${b.stress_level}%</div>
                <div>🔧 Type: ${b.workload_type || 'mixed'}</div>
                <div>🎯 Precision: ${b.precision || 'fp32'}</div>
                <div>⚡ PL: ${b.power_limit ? b.power_limit + ' W' : 'default'}</div>
                <div>⏱️ ${elapsed}s / ${b.duration}s (${pct}%)</div>
                <div>⏳ ${remaining}s left</div>
            </div>
            ${b.stop_reason ? `<div style="color:var(--danger);font-size:12px;margin-top:8px;padding:6px;background:rgba(220,53,69,.1);border-radius:4px">⚠️ ${escHtml(b.stop_reason)}</div>` : ''}
            <div class="progress-bar" style="margin-top:10px;height:6px">
                <div class="progress-fill ${statusClass === 'critical' ? 'danger' : ''}" style="width:${pct}%"></div>
            </div>`;
        activeBenchmarksDiv.appendChild(item);
    });
}

// ===== PRESETS =====
function applyPreset(type) {
    const presets = {
        light:   { stress: 25,  memory: 20,  workload: 'compute', precision: 'fp32', duration: 120, power: 200 },
        medium:  { stress: 50,  memory: 50,  workload: 'mixed',   precision: 'fp32', duration: 300, power: 250 },
        heavy:   { stress: 75,  memory: 75,  workload: 'mixed',   precision: 'fp32', duration: 600, power: 300 },
        extreme: { stress: 100, memory: 100, workload: 'mixed',   precision: 'fp16', duration: 300, power: 350 },
        memtest: { stress: 30,  memory: 100, workload: 'memory',  precision: 'fp32', duration: 300, power: 250 },
    };
    const p = presets[type];
    if (!p) return;
    document.getElementById('stress-level').value = p.stress;
    stressValue.textContent = p.stress + '%';
    document.getElementById('memory-level').value = p.memory;
    memoryValue.textContent = p.memory + '%';
    document.getElementById('workload-type').value = p.workload;
    document.getElementById('precision').value = p.precision;
    document.getElementById('duration').value = p.duration;
    powerLimitSlider.value = p.power;
    powerLimitValue.textContent = p.power + ' W';
    addLog('system', 'info', `Applied preset: ${type} (stress=${p.stress}%, memory=${p.memory}%, type=${p.workload}, PL=${p.power}W)`);
}

// ===== API CALLS =====
async function startBenchmark() {
    const selectedGPUs = Array.from(document.querySelectorAll('#gpu-selector input:checked')).map(i => parseInt(i.value));
    if (selectedGPUs.length === 0) { addLog('system', 'warning', 'Please select at least one GPU'); return; }
    const body = {
        gpu_indices: selectedGPUs,
        duration: parseInt(document.getElementById('duration').value),
        stress_level: parseInt(document.getElementById('stress-level').value),
        workload_type: document.getElementById('workload-type').value,
        precision: document.getElementById('precision').value,
        memory_level: parseInt(document.getElementById('memory-level').value),
        power_limit: parseInt(powerLimitSlider.value),
    };
    addBenchmarkLog('info', `Starting benchmark on GPUs: ${selectedGPUs.join(', ')} | Type: ${body.workload_type} | Stress: ${body.stress_level}% | PL: ${body.power_limit}W`);
    try {
        const res = await fetch('/api/benchmark/start', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
        const data = await res.json();
        if (res.ok) addBenchmarkLog('info', `Benchmark started: ${data.benchmark_id}`);
        else addBenchmarkLog('error', `Failed to start: ${data.error}`);
    } catch(e) { addBenchmarkLog('error', `Error: ${e.message}`); }
}

async function stopBenchmark(id) {
    try {
        const res = await fetch(`/api/benchmark/stop/${id}`, { method:'POST' });
        const data = await res.json();
        if (res.ok) addBenchmarkLog('info', `Stopped benchmark: ${id}`);
        else addBenchmarkLog('error', `Failed to stop: ${data.error}`);
    } catch(e) { addBenchmarkLog('error', `Error: ${e.message}`); }
}

async function stopAllBenchmarks() {
    if (!Object.keys(activeBenchmarks).length) { addLog('system', 'warning', 'No active benchmarks'); return; }
    for (const id of Object.keys(activeBenchmarks)) await stopBenchmark(id);
}

async function setFanSpeed(gpuId, speed) {
    try {
        const res = await fetch('/api/fan/set', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ gpu_id: gpuId, speed: parseInt(speed) }) });
        const data = await res.json();
        if (res.ok) addLog('system', 'info', `Fan GPU ${gpuId} set to ${speed}%`);
        else addLog('system', 'error', `Fan set failed: ${data.error}`);
    } catch(e) { addLog('system', 'error', `Fan error: ${e.message}`); }
}

async function applyManualFan(gpuId) {
    const slider = document.getElementById(`fan-slider-${gpuId}`);
    if (!slider) return;
    await setFanSpeed(gpuId, parseInt(slider.value));
}

async function resetFanControl(gpuId) {
    try {
        const res = await fetch('/api/fan/reset', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ gpu_id: gpuId }) });
        const data = await res.json();
        if (res.ok) {
            autoFanStatus[gpuId] = false;
            updateFanCardUI(gpuId, false);
            addLog('system', 'info', `Fan GPU ${gpuId} reset to driver auto`);
        } else addLog('system', 'error', `Fan reset failed: ${data.error}`);
    } catch(e) { addLog('system', 'error', `Fan error: ${e.message}`); }
}

async function toggleAutoFan(gpuId) {
    const current = autoFanStatus[gpuId] || false;
    const newState = !current;
    try {
        const res = await fetch('/api/fan/auto', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ gpu_id: gpuId, enabled: newState })
        });
        const data = await res.json();
        if (res.ok) {
            autoFanStatus[gpuId] = newState;
            updateFanCardUI(gpuId, newState);
            addLog('system', 'info', `GPU ${gpuId} fan curve: ${newState ? 'AUTO ON' : 'AUTO OFF'}`);
        } else {
            addLog('system', 'error', `Fan auto failed: ${data.error}`);
        }
    } catch(e) { addLog('system', 'error', `Fan error: ${e.message}`); }
}

function updateFanCardUI(gpuId, isAuto) {
    const btn = document.getElementById(`fan-auto-btn-${gpuId}`);
    const manual = document.getElementById(`fan-manual-${gpuId}`);
    const hint = btn ? btn.nextElementSibling : null;
    if (btn) {
        btn.className = `btn ${isAuto ? 'btn-primary' : 'btn-secondary'}`;
        btn.textContent = isAuto ? '🟢 Auto Curve ON' : '⬜ Auto Curve OFF';
    }
    if (hint) hint.textContent = isAuto ? 'Adjusting fan by temperature automatically' : 'Click to enable temperature tracking';
    if (manual) {
        manual.style.opacity = isAuto ? '0.45' : '1';
        manual.style.pointerEvents = isAuto ? 'none' : '';
    }
}

async function loadFanAutoStatus() {
    try {
        const res = await fetch('/api/fan/auto');
        if (!res.ok) return;
        const data = await res.json();
        Object.entries(data).forEach(([k, v]) => {
            autoFanStatus[parseInt(k)] = v;
            updateFanCardUI(parseInt(k), v);
        });
    } catch(e) { /* silently ignore */ }
}

async function saveConfiguration() {
    const body = { safety: { max_temperature: parseInt(document.getElementById('max-temp').value), critical_temperature: parseInt(document.getElementById('critical-temp').value), auto_stop_benchmark_on_critical: document.getElementById('auto-stop').checked } };
    try {
        const res = await fetch('/api/config/update', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
        const data = await res.json();
        if (res.ok) addLog('system', 'info', 'Configuration saved');
        else addLog('system', 'error', `Config save failed: ${data.error}`);
    } catch(e) { addLog('system', 'error', `Config error: ${e.message}`); }
}

// ===== SYSTEM TAB =====
async function loadSystemInfo() {
    try {
        const res = await fetch('/api/system/info');
        const info = await res.json();

        document.getElementById('driver-info').innerHTML = `
            <div class="info-row"><span class="info-key">Driver Version</span><span class="info-val">${info.driver_version}</span></div>
            <div class="info-row"><span class="info-key">CUDA Version</span><span class="info-val">${info.cuda_version}</span></div>
            <div class="info-row"><span class="info-key">GPU Count</span><span class="info-val">${info.gpu_count}</span></div>
            <div class="info-row"><span class="info-key">NVML Version</span><span class="info-val">${info.nvml_version}</span></div>`;

        document.getElementById('os-info').innerHTML = `
            <div class="info-row"><span class="info-key">OS</span><span class="info-val" style="font-size:11px">${info.os}</span></div>
            <div class="info-row"><span class="info-key">Hostname</span><span class="info-val">${info.hostname}</span></div>`;

        document.getElementById('python-info').innerHTML = `
            <div class="info-row"><span class="info-key">Python</span><span class="info-val">${info.python}</span></div>
            <div class="info-row"><span class="info-key">CuPy</span><span class="info-val ${info.cupy_installed ? 'ok' : 'bad'}">${info.cupy_installed ? info.cupy_version + ' ✓' : 'Not installed ✗'}</span></div>`;

        const grid = document.getElementById('gpu-details-grid');
        grid.innerHTML = '';
        (info.gpu_list || []).forEach((g, i) => {
            const card = document.createElement('div');
            card.className = 'gpu-detail-card';
            const vramGb = (parseInt(g.vram_mb) / 1024).toFixed(1);
            card.innerHTML = `<h3>GPU ${i}: ${g.name}</h3>
                <div class="info-list">
                    <div class="info-row"><span class="info-key">VRAM</span><span class="info-val">${vramGb} GB</span></div>
                    <div class="info-row"><span class="info-key">Compute Cap.</span><span class="info-val">${g.compute_cap}</span></div>
                </div>`;
            grid.appendChild(card);
        });
    } catch(e) {
        document.getElementById('driver-info').innerHTML = `<div class="info-row"><span class="info-val bad">Error loading info</span></div>`;
    }
}

async function runHealthCheck() {
    const resultsDiv = document.getElementById('health-results');
    resultsDiv.innerHTML = '<p style="color:var(--text2)">Running health check...</p>';
    try {
        const res = await fetch('/api/system/health');
        const data = await res.json();
        let html = '';
        data.gpus.forEach(gpu => {
            const icon = gpu.status === 'ok' ? '✅' : gpu.status === 'warning' ? '⚠️' : '❌';
            html += `<div class="health-gpu">
                <div class="health-gpu-title">${icon} GPU ${gpu.gpu_index}: ${gpu.name || 'Unknown'} — <span class="info-val ${gpu.status === 'ok' ? 'ok' : gpu.status === 'warning' ? 'warn' : 'bad'}">${gpu.status.toUpperCase()}</span></div>
                <div class="health-checks">
                    ${(gpu.checks || []).map(c => `<span class="health-check-item ${c.ok ? 'ok' : 'fail'}">${c.ok ? '✓' : '✗'} ${c.name}</span>`).join('')}
                    ${gpu.error ? `<span class="health-check-item fail">Error: ${escHtml(gpu.error)}</span>` : ''}
                </div>
            </div>`;
        });
        html += `<div class="info-row" style="margin-top:10px"><span class="info-key">CuPy (GPU Stress)</span><span class="info-val ${data.cupy_installed ? 'ok' : 'warn'}">${data.cupy_installed ? '✅ Installed' : '⚠️ Not installed — benchmark will use CPU fallback'}</span></div>`;
        resultsDiv.innerHTML = html;
    } catch(e) {
        resultsDiv.innerHTML = `<p style="color:var(--danger)">Health check failed: ${e.message}</p>`;
    }
}

function copyCode(btn) {
    const pre = btn.parentElement.querySelector('pre');
    navigator.clipboard.writeText(pre.textContent).then(() => {
        btn.textContent = '✓ Copied!';
        setTimeout(() => btn.textContent = '📋 Copy', 2000);
    });
}

// ===== RESULTS TAB =====
let resultCharts = {};

async function loadResults() {
    const container = document.getElementById('results-container');
    container.innerHTML = '<p style="color:var(--text2)">Loading results...</p>';

    try {
        const res = await fetch('/api/benchmarks/results');
        const results = await res.json();

        const ids = Object.keys(results);
        if (ids.length === 0) {
            container.innerHTML = '<p class="no-data">No completed benchmarks yet. Run a benchmark to see results here.</p>';
            return;
        }

        container.innerHTML = '';
        // Sort newest first
        ids.sort((a, b) => b.localeCompare(a));

        ids.forEach(bid => {
            const r = results[bid];
            const card = buildResultCard(bid, r);
            container.appendChild(card);
        });

        // Draw charts after DOM is ready
        setTimeout(() => {
            ids.forEach(bid => {
                if (results[bid].metrics_history) {
                    drawResultChart(bid, results[bid]);
                }
            });
        }, 50);

    } catch (e) {
        container.innerHTML = `<p style="color:var(--danger)">Error loading results: ${e.message}</p>`;
    }
}

function buildResultCard(bid, r) {
    const statusColor = {
        completed: '#76b900',
        stopped_critical_temp: '#ff5252',
        error: '#ff9800',
    }[r.status] || '#888';

    const duration = r.actual_duration ? r.actual_duration.toFixed(1) : r.duration;
    const gpus = (r.gpu_indices || []).join(', ');
    const startTime = r.start_time ? new Date(r.start_time).toLocaleString() : '-';

    const card = document.createElement('div');
    card.className = 'result-card';
    card.innerHTML = `
        <div class="result-card-header">
            <div class="result-id">${bid}</div>
            <div class="result-status" style="color:${statusColor}">${r.status}</div>
        </div>
        <div class="result-meta">
            <div>🎮 GPUs: ${gpus}</div>
            <div>⚡ Stress: ${r.stress_level}%</div>
            <div>🔧 Type: ${r.workload_type || 'mixed'}</div>
            <div>🎯 Precision: ${r.precision || 'fp32'}</div>
            <div>💾 Memory: ${r.memory_level || 50}%</div>
            <div>⚡ PL: ${r.power_limit ? r.power_limit + ' W' : 'default'}</div>
            <div>⏱️ Duration: ${duration}s</div>
            <div>🕐 Started: ${startTime}</div>
        </div>
        ${r.stop_reason ? `<div class="result-stop-reason">⚠️ ${escHtml(r.stop_reason)}</div>` : ''}
        ${r.metrics_history && r.metrics_history.length > 0 ? `
        <div class="result-charts">
            <div class="result-chart-wrap"><canvas id="result-chart-temp-${bid}"></canvas></div>
            <div class="result-chart-wrap"><canvas id="result-chart-util-${bid}"></canvas></div>
            <div class="result-chart-wrap"><canvas id="result-chart-power-${bid}"></canvas></div>
            <div class="result-chart-wrap"><canvas id="result-chart-fan-${bid}"></canvas></div>
        </div>` : '<p style="color:var(--text2);font-size:12px;margin-top:10px">No metrics data recorded</p>'}
    `;
    return card;
}

function drawResultChart(bid, r) {
    const history = r.metrics_history;
    if (!history || history.length === 0) return;

    const labels = history.map(s => s.ts.toFixed(0) + 's');
    const gpuIndices = r.gpu_indices || [];

    const definitions = [
        { suffix: 'temp',  title: '🌡️ Temperature (°C)', key: 'temp',  max: 110, color: ['#ff5252','#2196F3','#76b900','#ff9800'] },
        { suffix: 'util',  title: '⚡ Utilization (%)',   key: 'util',  max: 100, color: ['#76b900','#2196F3','#ff5252','#ff9800'] },
        { suffix: 'power', title: '🔋 Power (W)',          key: 'power', max: 450, color: ['#ff9800','#9C27B0','#76b900','#2196F3'] },
        { suffix: 'fan',   title: '🌀 Fan Speed (%)',      key: 'fan',   max: 100, color: ['#00BCD4','#2196F3','#76b900','#ff5252'] },
    ];

    definitions.forEach(def => {
        const canvasId = `result-chart-${def.suffix}-${bid}`;
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        // Destroy old chart if exists
        if (resultCharts[canvasId]) resultCharts[canvasId].destroy();

        const datasets = gpuIndices.map((gpuIdx, i) => ({
            label: `GPU ${gpuIdx}`,
            data: history.map(s => {
                const g = s.gpus.find(g => g.gpu === gpuIdx);
                return g ? g[def.key] : null;
            }),
            borderColor: def.color[i % def.color.length],
            backgroundColor: 'transparent',
            tension: 0.3,
            pointRadius: 0,
            borderWidth: 2,
        }));

        resultCharts[canvasId] = new Chart(canvas, {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                animation: false,
                plugins: {
                    legend: { labels: { color: '#888', boxWidth: 10, font: { size: 11 } } },
                    title: { display: true, text: def.title, color: '#76b900', font: { size: 12 } },
                },
                scales: {
                    x: { ticks: { color: '#666', maxTicksLimit: 10, font: { size: 10 } }, grid: { color: '#222' } },
                    y: { ticks: { color: '#888', font: { size: 10 } }, grid: { color: '#222' }, min: 0, suggestedMax: def.max },
                },
            }
        });
    });
}

function clearResults() {
    Object.values(resultCharts).forEach(c => c.destroy());
    resultCharts = {};
    document.getElementById('results-container').innerHTML = '<p class="no-data">Results cleared from view. Completed runs remain on server until restart.</p>';
}
