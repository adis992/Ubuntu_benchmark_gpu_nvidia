🎮 NVIDIA GPU Benchmark Tool
🚀 Quick Start
# NVIDIA GPU Benchmark Tool

Professional GPU benchmarking and monitoring tool for NVIDIA graphics cards on Ubuntu/Linux systems.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)
![NVIDIA](https://img.shields.io/badge/NVIDIA-GPU-76B900.svg)

## Quick Start

### Installation

1. Clone the repository.

```bash
git clone https://github.com/adis992/Ubuntu_benchmark_gpu_nvidia.git
cd Ubuntu_benchmark_gpu_nvidia
```

2. Install and start the service.

```bash
sudo ./install.sh
```

Installer actions:
- Installs Linux dependencies
- Creates Python virtual environment
- Installs Python packages
- Registers systemd service
- Starts service automatically

3. Open dashboard panel.

- Local machine: http://localhost:5000
- Remote machine: http://YOUR_SERVER_IP:5000

If installed on a remote server, ensure port 5000 is reachable from browser.

## Dashboard Preview

![Dashboard Screenshot 1](Screenshot%20from%202026-05-09%2010-15-01.png)
![Dashboard Screenshot 2](Screenshot%20from%202026-05-09%2010-15-10.png)
![Dashboard Screenshot 3](Screenshot%20from%202026-05-09%2010-15-40.png)
![Dashboard Screenshot 4](Screenshot%20from%202026-05-09%2010-16-40.png)

## Features

### Real-time GPU Monitoring
- Live metrics: temperature, utilization, memory usage, power
- Multi-GPU support
- Clock speed tracking
- Fan speed monitoring

### Professional Benchmarking
- Stress level control (1-100 percent)
- Duration control (1 second to 24 hours)
- Single or multiple GPU selection
- Workload and precision selection
- Metrics history in results view

### Power Limit Control
- Default power limit set to 300 W in dashboard
- Manual per-run power limit selection
- Power limit restore at benchmark end
- Overlapping benchmark handling to avoid power-limit race conditions

### Fan Control
- Auto fan curve mode
- Manual fixed fan speed mode
- Automatic reset to driver auto at benchmark end

Auto fan curve:
- Below 50 C -> 30 percent
- 50 C -> 55 percent
- +1 percent for each degree above 50 C
- 95 C -> 100 percent

### Safety Features
- Configurable max and critical temperatures
- Auto-stop on critical temperature
- Crash and critical event logging

## First Run Checklist

- Confirm NVIDIA driver works: `nvidia-smi`
- Open panel and verify all GPUs are visible
- Keep Power Limit at 300 W for first test
- Run short benchmark: 30-60 seconds

Recommended first benchmark:

```text
Duration: 60
Stress: 90-100%
Workload: mixed
Precision: fp32
Power Limit: 300 W
```

## Usage

### Start a Benchmark
1. Select GPUs.
2. Set duration.
3. Choose workload and precision.
4. Set power limit.
5. Click start and monitor live cards.

### Stop a Benchmark
- Stop individual benchmark from Active Benchmarks panel
- Stop all benchmarks from control panel

### Manual Start without Service

```bash
./start.sh
```

## Service Management

```bash
# Start service
sudo systemctl start nvidia-gpu-benchmark

# Stop service
sudo systemctl stop nvidia-gpu-benchmark

# Restart service
sudo systemctl restart nvidia-gpu-benchmark

# Check status
sudo systemctl status nvidia-gpu-benchmark

# Follow service logs
sudo journalctl -u nvidia-gpu-benchmark -f

# Follow app log
tail -f /opt/nvidia-gpu-benchmark/logs/server.log

# Enable/disable startup
sudo systemctl enable nvidia-gpu-benchmark
sudo systemctl disable nvidia-gpu-benchmark
```

## API Endpoints

### REST API
- GET /api/status
- GET /api/gpus
- GET /api/gpu/<id>
- POST /api/benchmark/start
- POST /api/benchmark/stop/<id>
- GET /api/benchmarks/active
- GET /api/benchmarks/results
- GET /api/power/limits
- POST /api/power/set
- POST /api/power/reset
- POST /api/fan/set
- POST /api/fan/reset
- GET /api/fan/auto
- POST /api/fan/auto
- GET /api/config
- POST /api/config/update
- GET /api/system/info
- GET /api/system/health

### WebSocket Events
- connect
- disconnect
- start_monitoring
- stop_monitoring
- gpu_update (server -> client)

## Configuration

Edit `config.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  },
  "benchmark": {
    "default_duration": 300,
    "max_duration": 86400
  },
  "monitoring": {
    "poll_interval": 0.5
  },
  "safety": {
    "max_temperature": 100,
    "critical_temperature": 105,
    "auto_stop_benchmark_on_critical": true
  }
}
```

## Troubleshooting

### Service does not start

```bash
sudo journalctl -u nvidia-gpu-benchmark -n 50
```

Common causes:
- NVIDIA drivers missing
- Port 5000 already in use
- Dependencies missing

### Power limit looks wrong during benchmark
- Ensure no old benchmark is still active on same GPU
- Stop all active benchmarks before new test
- Refresh dashboard after start
- Check logs for power-limit set/restore lines

### Fan control not working
- Requires compatible NVIDIA driver and GPU support
- Some GPUs do not allow manual software fan control
- Use driver auto mode if manual mode fails

### Permission denied

```bash
sudo chown -R $USER:$USER /opt/nvidia-gpu-benchmark
```

## Project Structure

```text
nvidia-gpu-benchmark/
├── server.py
├── gpu_monitor.py
├── benchmark.py
├── config.json
├── requirements.txt
├── install.sh
├── start.sh
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── logs/
```

## Requirements

- Ubuntu 20.04+ or compatible Debian-based Linux
- NVIDIA GPU
- NVIDIA driver with `nvidia-smi`
- Python 3.8+
- Sudo access for installation and service operations

## License

MIT License.

## Disclaimer

- Use at your own risk
- Monitor temperatures during stress tests
- Benchmarking increases power consumption and heat
Professional GPU monitoring shouldn't be complicated.