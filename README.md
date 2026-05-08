# 🎮 NVIDIA GPU Benchmark Tool

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

1. **Clone or download this repository**
```bash
cd /home/noname/Ubuntu_benchmark_gpu_nvidia
```

2. **Run the installation script**
```bash
sudo ./install.sh
```

The installation script will:
- Install system dependencies
- Create Python virtual environment
- Install Python packages
- Set up systemd service
- Start the service automatically

3. **Access the dashboard**

Open your browser and navigate to:
- `http://localhost:5000`
- Or from another device: `http://YOUR_SERVER_IP:5000`

### Manual Start (Without Service)

If you prefer to run manually without installing as a service:

```bash
./start.sh
```

## 📖 Usage Guide

### Starting a Benchmark

1. **Select GPUs**: Check the boxes for GPUs you want to benchmark
2. **Set duration**: Enter benchmark duration in seconds (default: 300)
3. **Choose stress level**: Adjust the slider (1-100%, default: 100%)
4. **Configure safety**: Set temperature limits if needed
5. **Click "Start Benchmark"**: Monitor progress in real-time

### Monitoring GPUs

The dashboard automatically displays:
- Current temperature with color-coded warnings
- GPU and memory utilization percentages
- Memory usage (used/total)
- Power consumption and limits
- Fan speeds
- Clock frequencies

### Fan Control

**Note**: Fan control requires specific driver support and elevated permissions.

1. **Manual mode**: Drag the fan slider for each GPU
2. **Automatic mode**: Click the "Auto" button to return to driver control

### Safety Settings

Configure thermal protection:
- **Max Temperature**: Warning threshold (default: 85°C)
- **Critical Temperature**: Emergency shutdown threshold (default: 90°C)
- **Auto-shutdown**: Enable automatic benchmark stop on critical temp

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

# Disable auto-start
sudo systemctl disable nvidia-gpu-benchmark

# Enable auto-start
sudo systemctl enable nvidia-gpu-benchmark
```

### Log Files

Logs are stored in the `logs/` directory:
- `server.log`: Main application log
- `service.log`: Systemd service output
- `service_error.log`: Systemd service errors
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
    "max_temperature": 85,
    "critical_temperature": 90,
    "auto_shutdown_on_critical": true
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
