# 🎮 NVIDIA GPU Benchmark Tool

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/adis992/Ubuntu_benchmark_gpu_nvidia.git
cd Ubuntu_benchmark_gpu_nvidia
```

2. Install the tool:
```bash
sudo ./install.sh
```

The installer will:
- install Linux dependencies
- create the Python virtual environment
- install Python packages
- register the systemd service
- start the service automatically

3. Open the dashboard panel:
- Local machine: [http://localhost:5000](http://localhost:5000)
- Remote machine: [http://YOUR_SERVER_IP:5000](http://YOUR_SERVER_IP:5000)

If you installed on a remote server, make sure port `5000` is reachable from your browser.


Professional GPU benchmarking and monitoring tool for NVIDIA graphics cards on Ubuntu/Linux systems.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![NVIDIA](https://img.shields.io/badge/NVIDIA-GPU-76B900.svg)

## ✨ Features

### 🖥️ Real-time GPU Monitoring
- **Live metrics**: Temperature, utilization, memory usage, power consumption
- **Multi-GPU support**: Monitor and benchmark multiple GPUs simultaneously
- **Clock speeds**: Track GPU and memory clock frequencies
- **Fan speed monitoring**: Real-time fan RPM/percentage tracking

### 🚀 Professional Benchmarking
- **Flexible stress testing**: Choose stress levels from 1% to 100%
- **Time-based testing**: Set custom duration (1 second to 24 hours)
- **GPU selection**: Benchmark individual GPUs or multiple at once
- **Load patterns**: Various workload intensities

### 🛡️ Safety Features
- **Temperature monitoring**: Configurable max and critical temperature thresholds
- **Auto-shutdown**: Automatic benchmark termination on critical temperature
- **Crash detection**: Pre-crash logging to identify hardware issues
- **Thermal protection**: Prevents GPU damage from excessive heat

### 🌀 Fan Control
- **Manual control**: Set custom fan speeds (0-100%)
- **Automatic mode**: Return to driver-controlled fan management
- **Real-time adjustment**: Change fan speeds during benchmarks

### 📊 Web Dashboard
- **Modern UI**: Clean, professional interface
- **Real-time updates**: Live data via WebSocket
- **No black screens**: Stable monitoring without display interruptions
- **Responsive design**: Works on desktop and mobile browsers

### 📝 Advanced Logging
- **Comprehensive logs**: All events logged with timestamps
- **Crash detection**: Automatic logging before system crashes
- **Error tracking**: Detailed error messages and stack traces
- **Service logs**: Systemd integration for system-level logging

### ⚙️ System Integration
- **Systemd service**: Auto-start on boot
- **Background operation**: Runs as system service
- **Easy installation**: One-command setup script
- **Manual mode**: Option to run without service installation

## 📋 Requirements

- **OS**: Ubuntu 20.04+ or other Debian-based Linux distributions
- **GPU**: NVIDIA graphics card (tested with RTX 3090)
- **Drivers**: NVIDIA drivers with `nvidia-smi` available
- **Python**: Python 3.8 or higher
- **Permissions**: Root access for installation (sudo)

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/adis992/Ubuntu_benchmark_gpu_nvidia.git
cd Ubuntu_benchmark_gpu_nvidia
```

2. Install the tool:
```bash
sudo ./install.sh
```

The installer will:
- install Linux dependencies
- create the Python virtual environment
- install Python packages
- register the systemd service
- start the service automatically

3. Open the dashboard panel:
- Local machine: [http://localhost:5000](http://localhost:5000)
- Remote machine: [http://YOUR_SERVER_IP:5000](http://YOUR_SERVER_IP:5000)

If you installed on a remote server, make sure port `5000` is reachable from your browser.

### Manual Start (Without Service)

If you prefer not to install the systemd service:

```bash
./start.sh
```

### First Run Checklist

- Confirm `nvidia-smi` works
- Open the panel and verify both GPUs are visible
- Keep Power Limit at the default `300 W` for the first test
- Start with a short benchmark duration such as `30` to `60` seconds

## 📖 Usage Guide

### Starting a Benchmark

1. Select the GPUs you want to stress.
2. Set benchmark duration.
3. Choose workload type and precision.
4. Set the Power Limit. Default is `300 W`.
5. Start the benchmark and watch the live GPU cards update in real time.

Recommended first test:
```bash
Duration: 60
Stress: 90-100%
Workload: mixed
Precision: fp32
Power Limit: 300 W
```

### Monitoring GPUs

The dashboard automatically displays:
- Current temperature with color-coded warnings
- GPU and memory utilization percentages
- Memory usage (used/total)
- Power consumption and limits
- Fan speeds
- Clock frequencies

### Fan Control

**Note**: Fan control requires NVIDIA driver support and may need elevated permissions depending on your system.

The dashboard now supports two fan modes:

- **Auto Curve**: temperature-based fan curve
  - below `50°C` → `30%`
  - `50°C` → `55%`
  - increases by `1%` per degree above `50°C`
  - `95°C` → `100%`
- **Manual**: fixed fan speed set per GPU from the fan control panel

Use Auto Curve for normal testing and manual mode only when you want a constant fixed fan speed.

### Safety Settings

Configure thermal protection:
- **Max Temperature**: Warning threshold (default: 100°C)
- **Critical Temperature**: Emergency shutdown threshold (default: 105°C)
- **Auto-shutdown**: Enable automatic benchmark stop on critical temp
- **Power Limit**: Set a safe operating limit before starting the test

Click "Save Settings" to apply changes.

### Stopping Benchmarks

- **Stop individual**: Click "Stop" button on specific benchmark
- **Stop all**: Click "Stop All" button in control panel

## 🔧 Service Management

### Systemd Commands

```bash
# Start service
sudo systemctl start nvidia-gpu-benchmark

# Stop service
sudo systemctl stop nvidia-gpu-benchmark

# Restart service
sudo systemctl restart nvidia-gpu-benchmark

# Check status
sudo systemctl status nvidia-gpu-benchmark

# View logs
sudo journalctl -u nvidia-gpu-benchmark -f

# View application log
tail -f /opt/nvidia-gpu-benchmark/logs/server.log

# Disable auto-start
sudo systemctl disable nvidia-gpu-benchmark

# Enable auto-start
sudo systemctl enable nvidia-gpu-benchmark
```

### Log Files

Logs are stored in the `logs/` directory:
- `server.log`: Main application log
- `crash_detection.log`: Critical events and crashes

## 🏗️ Architecture

```
nvidia-gpu-benchmark/
├── server.py              # Flask server with REST API and WebSocket
├── gpu_monitor.py         # NVIDIA GPU monitoring using pynvml
├── benchmark.py           # Benchmark workload and crash detection
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
├── install.sh            # Installation script
├── start.sh              # Manual start script
├── templates/
│   └── index.html        # Web dashboard HTML
├── static/
│   ├── css/
│   │   └── style.css     # Dashboard styles
│   └── js/
│       └── app.js        # Frontend JavaScript
└── logs/                 # Log files directory
```

## 🔌 API Endpoints

### REST API

- `GET /api/status` - System status
- `GET /api/gpus` - All GPU information
- `GET /api/gpu/<id>` - Specific GPU details
- `POST /api/benchmark/start` - Start benchmark
- `POST /api/benchmark/stop/<id>` - Stop benchmark
- `GET /api/benchmarks/active` - Active benchmarks
- `GET /api/benchmarks/results` - Benchmark results
- `POST /api/fan/set` - Set fan speed
- `POST /api/fan/reset` - Reset fan control
- `GET /api/fan/auto` - Get auto fan curve status
- `POST /api/fan/auto` - Enable or disable auto fan curve
- `GET /api/config` - Get configuration
- `POST /api/config/update` - Update configuration

### WebSocket Events

- `connect` - Client connection
- `disconnect` - Client disconnection
- `start_monitoring` - Start real-time updates
- `stop_monitoring` - Stop real-time updates
- `gpu_update` - GPU data broadcast (server → client)

## ⚙️ Configuration

Edit `config.json` to customize settings:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  },
  "benchmark": {
    "default_duration": 300,
    "max_duration": 86400,
    "stress_levels": {
      "low": 30,
      "medium": 60,
      "high": 85,
      "extreme": 100
    }
  },
  "safety": {
    "max_temperature": 100,
    "critical_temperature": 105,
    "auto_stop_benchmark_on_critical": true
  }
}
```

## 🐛 Troubleshooting

### Service won't start

Check logs:
```bash
sudo journalctl -u nvidia-gpu-benchmark -n 50
```

Common issues:
- NVIDIA drivers not installed: `sudo apt install nvidia-driver-XXX`
- Port 5000 already in use: Change port in `config.json`
- Missing dependencies: Run `pip install -r requirements.txt`

### Benchmark starts but power limit looks wrong

If a benchmark starts with a power limit but the GPU still shows a different value:
- make sure no other benchmark is still running on the same GPU
- stop all active benchmarks before starting a new one
- refresh the dashboard after start

The tool now waits for overlapping benchmarks to clear, but an old long-running run can still hold the GPU if it was started manually.

### No GPUs detected

Verify NVIDIA drivers:
```bash
nvidia-smi
```

If this fails, reinstall NVIDIA drivers.

### Fan control not working

Fan control requires:
- Specific NVIDIA driver support
- Elevated permissions
- Compatible GPU model

Some GPUs don't support manual fan control via software.

### Permission denied errors

Ensure proper permissions:
```bash
sudo chown -R $USER:$USER /opt/nvidia-gpu-benchmark
```

## 🤝 Contributing

This tool is designed to help Ubuntu desktop users who lack professional GPU monitoring tools. Contributions are welcome!

## 📄 License

This project is open source and available under the MIT License.

## ⚠️ Disclaimer

- **Use at your own risk**: GPU benchmarking can stress hardware
- **Monitor temperatures**: High temperatures can damage components
- **Warranty**: Check your GPU warranty before intensive testing
- **Power consumption**: Benchmarking increases power usage
- **System stability**: May cause system instability on faulty hardware

## 🎯 Tested Hardware

- NVIDIA GeForce RTX 3090 (2x)
- Ubuntu 22.04 LTS
- NVIDIA Driver 535.x

Should work with most NVIDIA GPUs that support `nvidia-smi`.

## 📍 Panel URL

After installation, open the web panel here:

- [http://localhost:5000](http://localhost:5000) for the local machine
- [http://SERVER_IP:5000](http://SERVER_IP:5000) from another machine on the network

## 📞 Support

For issues, questions, or suggestions:
1. Check the troubleshooting section
2. Review log files in `logs/` directory
3. Check crash detection logs for hardware issues

## 🌟 Features Coming Soon

- [ ] Benchmark result history and graphs
- [ ] Email/notification alerts on critical events
- [ ] Custom CUDA benchmark kernels
- [ ] Multi-machine monitoring
- [ ] Export benchmark results (CSV, JSON)
- [ ] Comparison with baseline results
- [ ] GPU health scoring

---

**Made with ❤️ for the Linux community**

*Professional GPU monitoring shouldn't be complicated.*
