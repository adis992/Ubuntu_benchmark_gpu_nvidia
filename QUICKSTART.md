# Quick Start Guide

## 🚀 Installation (One Command)

```bash
sudo ./install.sh
```

That's it! The dashboard will be available at `http://localhost:5000`

## 📝 Prerequisites

- Ubuntu 20.04+ or Debian-based Linux
- NVIDIA GPU with drivers installed
- Python 3.8+
- Root access (for installation)

## 🎯 Usage

### Access Dashboard
Open your browser: `http://localhost:5000`

### Basic Benchmark
1. Select GPU(s) to test
2. Set duration (in seconds)
3. Choose stress level (1-100%)
4. Click "Start Benchmark"

### Manual Start (No Service)
```bash
./start.sh
```

### Service Control
```bash
# Start
sudo systemctl start nvidia-gpu-benchmark

# Stop
sudo systemctl stop nvidia-gpu-benchmark

# Status
sudo systemctl status nvidia-gpu-benchmark

# Logs
sudo journalctl -u nvidia-gpu-benchmark -f
```

## 🔧 Testing

Run a quick system test:
```bash
./test.sh
```

Check system information:
```bash
./system_info.sh
```

## 📊 Features

✅ Real-time GPU monitoring  
✅ Multi-GPU support  
✅ Temperature tracking with alerts  
✅ Fan control  
✅ Benchmark stress testing  
✅ Crash detection & logging  
✅ Auto-shutdown on critical temperature  
✅ Web-based dashboard  
✅ No black screens  

## ⚠️ Safety

- Default max temp: 85°C
- Critical temp: 90°C
- Auto-shutdown enabled by default
- All temperatures monitored in real-time

## 🆘 Troubleshooting

**GPU not detected?**
```bash
nvidia-smi  # Should show your GPU
```

**Port 5000 in use?**
Edit `config.json` and change the port number

**Service won't start?**
```bash
sudo journalctl -u nvidia-gpu-benchmark -n 50
```

## 📚 More Info

See [README.md](README.md) for detailed documentation.

## 🗑️ Uninstall

```bash
sudo ./uninstall.sh
```
