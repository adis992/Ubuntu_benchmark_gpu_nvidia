// GPU Benchmark Tool - Frontend JavaScript

const socket = io();
let gpuData = [];
let activeBenchmarks = {};

// DOM Elements
const connectionStatus = document.getElementById('connection-status');
const connectionText = document.getElementById('connection-text');
const gpuCount = document.getElementById('gpu-count');
const currentTime = document.getElementById('current-time');
const gpuSelector = document.getElementById('gpu-selector');
const gpusContainer = document.getElementById('gpus-container');
const activeBenchmarksDiv = document.getElementById('active-benchmarks');
const logsContainer = document.getElementById('logs-container');
const stressLevel = document.getElementById('stress-level');
const stressValue = document.getElementById('stress-value');
const startBenchmarkBtn = document.getElementById('start-benchmark');
const stopAllBenchmarksBtn = document.getElementById('stop-all-benchmarks');
const saveConfigBtn = document.getElementById('save-config');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    updateTime();
    setInterval(updateTime, 1000);
});

// Socket.IO Events
socket.on('connect', () => {
    connectionStatus.classList.add('connected');
    connectionText.textContent = 'Connected';
    addLog('Connected to server', 'info');
    socket.emit('start_monitoring');
});

socket.on('disconnect', () => {
    connectionStatus.classList.remove('connected');
    connectionText.textContent = 'Disconnected';
    addLog('Disconnected from server', 'error');
});

socket.on('gpu_update', (data) => {
    gpuData = data.gpus || [];
    activeBenchmarks = data.benchmarks || {};
    updateGPUDisplay();
    updateActiveBenchmarks();
    updateGPUCount();
});

socket.on('monitoring_status', (data) => {
    if (data.active) {
        addLog('Monitoring started', 'info');
    } else {
        addLog('Monitoring stopped', 'info');
    }
});

// Setup Event Listeners
function setupEventListeners() {
    stressLevel.addEventListener('input', (e) => {
        stressValue.textContent = `${e.target.value}%`;
    });

    startBenchmarkBtn.addEventListener('click', startBenchmark);
    stopAllBenchmarksBtn.addEventListener('click', stopAllBenchmarks);
    saveConfigBtn.addEventListener('click', saveConfiguration);
}

// Update Functions
function updateTime() {
    const now = new Date();
    currentTime.textContent = now.toLocaleTimeString();
}

function updateGPUCount() {
    gpuCount.textContent = gpuData.length;
}

function updateGPUDisplay() {
    if (gpuData.length === 0) {
        gpusContainer.innerHTML = '<p class="no-data">No GPUs detected. Make sure NVIDIA drivers are installed.</p>';
        gpuSelector.innerHTML = '<p class="no-data">No GPUs available</p>';
        return;
    }

    // Update GPU selector
    if (gpuSelector.children.length === 0) {
        gpuData.forEach((gpu, index) => {
            const label = document.createElement('label');
            label.className = 'gpu-checkbox';
            label.innerHTML = `
                <input type="checkbox" value="${gpu.index}" checked>
                <span>GPU ${gpu.index}: ${gpu.name}</span>
            `;
            gpuSelector.appendChild(label);
        });
    }

    // Update GPU cards
    gpusContainer.innerHTML = '';
    gpuData.forEach(gpu => {
        const card = createGPUCard(gpu);
        gpusContainer.appendChild(card);
    });
}

function createGPUCard(gpu) {
    const card = document.createElement('div');
    card.className = 'gpu-card';
    
    // Apply temperature-based styling
    if (gpu.temperature >= 105) {
        card.classList.add('critical');
    } else if (gpu.temperature >= 95) {
        card.classList.add('hot');
    }

    const tempClass = gpu.temperature >= 105 ? 'danger' : gpu.temperature >= 95 ? 'warning' : '';
    const utilizationClass = gpu.utilization.gpu >= 90 ? 'warning' : '';
    const memoryClass = gpu.memory.percent >= 90 ? 'warning' : '';

    card.innerHTML = `
        <div class="gpu-header">
            <div class="gpu-name">${gpu.name}</div>
            <div class="gpu-index">GPU ${gpu.index}</div>
        </div>
        
        <div class="gpu-stats">
            <div class="stat-item">
                <div class="stat-label">🌡️ Temperature</div>
                <div class="stat-value ${tempClass}">${gpu.temperature}°C</div>
                <div class="progress-bar">
                    <div class="progress-fill ${tempClass}" style="width: ${Math.min(gpu.temperature, 100)}%"></div>
                </div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">⚡ GPU Utilization</div>
                <div class="stat-value ${utilizationClass}">${gpu.utilization.gpu}%</div>
                <div class="progress-bar">
                    <div class="progress-fill ${utilizationClass}" style="width: ${gpu.utilization.gpu}%"></div>
                </div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">💾 Memory Usage</div>
                <div class="stat-value ${memoryClass}">${gpu.memory.used_mb.toFixed(0)} MB</div>
                <div class="progress-bar">
                    <div class="progress-fill ${memoryClass}" style="width: ${gpu.memory.percent}%"></div>
                </div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">🔋 Power Usage</div>
                <div class="stat-value">${gpu.power.usage.toFixed(1)} W</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${gpu.power.percent}%"></div>
                </div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">🌀 Fan Speed</div>
                <div class="stat-value">${gpu.fan_speed}%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${gpu.fan_speed}%"></div>
                </div>
            </div>
            
            <div class="stat-item">
                <div class="stat-label">⚙️ GPU Clock</div>
                <div class="stat-value">${gpu.clocks.graphics} MHz</div>
            </div>
        </div>
        
        <div class="fan-control">
            <div class="fan-control-header">
                <strong>🌀 Fan Control</strong>
                <button class="btn btn-secondary" onclick="resetFanControl(${gpu.index})">Auto</button>
            </div>
            <input type="range" class="fan-slider" min="0" max="100" value="${gpu.fan_speed}" 
                   onchange="setFanSpeed(${gpu.index}, this.value)">
            <small style="color: var(--text-secondary);">Note: Fan control requires elevated permissions</small>
        </div>
    `;

    return card;
}

function updateActiveBenchmarks() {
    const benchmarkKeys = Object.keys(activeBenchmarks);
    
    if (benchmarkKeys.length === 0) {
        activeBenchmarksDiv.innerHTML = '<p class="no-data">No active benchmarks</p>';
        return;
    }

    activeBenchmarksDiv.innerHTML = '';
    benchmarkKeys.forEach(benchmarkId => {
        const benchmark = activeBenchmarks[benchmarkId];
        const item = createBenchmarkItem(benchmarkId, benchmark);
        activeBenchmarksDiv.appendChild(item);
    });
}

function createBenchmarkItem(benchmarkId, benchmark) {
    const div = document.createElement('div');
    div.className = 'benchmark-item';
    
    const elapsed = benchmark.elapsed.toFixed(0);
    const remaining = Math.max(0, benchmark.duration - elapsed);
    const progress = (elapsed / benchmark.duration * 100).toFixed(1);
    
    // Check status for special cases
    let statusClass = 'running';
    let statusText = benchmark.status;
    let stopReasonHTML = '';
    
    if (benchmark.status === 'stopped_critical_temp') {
        statusClass = 'critical';
        statusText = 'STOPPED - Critical Temp';
        if (benchmark.stop_reason) {
            stopReasonHTML = `<div style="color: #dc3545; font-weight: bold; margin-top: 5px;">⚠️ ${benchmark.stop_reason}</div>`;
        }
    } else if (benchmark.status === 'completed') {
        statusClass = 'completed';
        statusText = 'Completed';
    }

    div.innerHTML = `
        <div class="benchmark-header">
            <div class="benchmark-id">${benchmarkId}</div>
            <div class="benchmark-status ${statusClass}">${statusText}</div>
            <button class="btn btn-danger" onclick="stopBenchmark('${benchmarkId}')">Stop</button>
        </div>
        <div class="benchmark-info">
            <div>📊 GPUs: ${benchmark.gpu_indices.join(', ')}</div>
            <div>⚡ Stress Level: ${benchmark.stress_level}%</div>
            <div>⏱️ Elapsed: ${elapsed}s / ${benchmark.duration}s (${progress}%)</div>
            <div>⏳ Remaining: ${remaining}s</div>
            ${stopReasonHTML}
        </div>
        <div class="progress-bar" style="margin-top: 10px;">
            <div class="progress-fill ${statusClass === 'critical' ? 'danger' : ''}" style="width: ${progress}%"></div>
        </div>
    `;

    return div;
}

function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('p');
    logEntry.className = `log-entry ${type}`;
    logEntry.textContent = `[${timestamp}] ${message}`;
    logsContainer.appendChild(logEntry);
    logsContainer.scrollTop = logsContainer.scrollHeight;

    // Keep only last 100 log entries
    while (logsContainer.children.length > 100) {
        logsContainer.removeChild(logsContainer.firstChild);
    }
}

// API Functions
async function startBenchmark() {
    const selectedGPUs = Array.from(document.querySelectorAll('#gpu-selector input:checked'))
        .map(input => parseInt(input.value));
    
    if (selectedGPUs.length === 0) {
        addLog('Please select at least one GPU', 'warning');
        return;
    }

    const duration = parseInt(document.getElementById('duration').value);
    const stress = parseInt(document.getElementById('stress-level').value);

    addLog(`Starting benchmark on GPUs: ${selectedGPUs.join(', ')}`, 'info');

    try {
        const response = await fetch('/api/benchmark/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                gpu_indices: selectedGPUs,
                duration: duration,
                stress_level: stress
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            addLog(`Benchmark started: ${data.benchmark_id}`, 'info');
        } else {
            addLog(`Failed to start benchmark: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`Error starting benchmark: ${error.message}`, 'error');
    }
}

async function stopBenchmark(benchmarkId) {
    try {
        const response = await fetch(`/api/benchmark/stop/${benchmarkId}`, {
            method: 'POST'
        });

        const data = await response.json();
        
        if (response.ok) {
            addLog(`Stopped benchmark: ${benchmarkId}`, 'info');
        } else {
            addLog(`Failed to stop benchmark: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`Error stopping benchmark: ${error.message}`, 'error');
    }
}

async function stopAllBenchmarks() {
    const benchmarkKeys = Object.keys(activeBenchmarks);
    
    if (benchmarkKeys.length === 0) {
        addLog('No active benchmarks to stop', 'warning');
        return;
    }

    for (const benchmarkId of benchmarkKeys) {
        await stopBenchmark(benchmarkId);
    }
}

async function setFanSpeed(gpuId, speed) {
    try {
        const response = await fetch('/api/fan/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                gpu_id: gpuId,
                speed: parseInt(speed)
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            addLog(`Set fan speed to ${speed}% on GPU ${gpuId}`, 'info');
        } else {
            addLog(`Failed to set fan speed: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`Error setting fan speed: ${error.message}`, 'error');
    }
}

async function resetFanControl(gpuId) {
    try {
        const response = await fetch('/api/fan/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ gpu_id: gpuId })
        });

        const data = await response.json();
        
        if (response.ok) {
            addLog(`Reset fan control to automatic on GPU ${gpuId}`, 'info');
        } else {
            addLog(`Failed to reset fan control: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`Error resetting fan control: ${error.message}`, 'error');
    }
}

async function saveConfiguration() {
    const maxTemp = parseInt(document.getElementById('max-temp').value);
    const criticalTemp = parseInt(document.getElementById('critical-temp').value);
    const autoStop = document.getElementById('auto-stop').checked;

    try {
        const response = await fetch('/api/config/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                safety: {
                    max_temperature: maxTemp,
                    critical_temperature: criticalTemp,
                    auto_stop_benchmark_on_critical: autoStop
                }
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            addLog('Configuration saved successfully', 'info');
        } else {
            addLog(`Failed to save configuration: ${data.error}`, 'error');
        }
    } catch (error) {
        addLog(`Error saving configuration: ${error.message}`, 'error');
    }
}
