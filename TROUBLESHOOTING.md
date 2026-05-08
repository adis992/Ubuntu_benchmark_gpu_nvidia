# 🛠️ Troubleshooting Guide

## Common Issues and Solutions

### 1. NVIDIA Drivers Not Found

**Error**: `nvidia-smi: command not found`

**Solution**:
```bash
# Check if NVIDIA GPU is detected
lspci | grep -i nvidia

# Install NVIDIA drivers
sudo ubuntu-drivers devices
sudo ubuntu-drivers autoinstall

# Or install specific version
sudo apt install nvidia-driver-535

# Reboot after installation
sudo reboot
```

### 2. Python Dependencies Issues

**Error**: `ModuleNotFoundError: No module named 'pynvml'`

**Solution**:
```bash
# Activate virtual environment (if installed)
cd /opt/nvidia-gpu-benchmark
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or install specific package
pip install nvidia-ml-py
```

### 3. Port 5000 Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Check what's using port 5000
sudo lsof -i :5000
# or
sudo netstat -tulpn | grep 5000

# Option 1: Kill the process
sudo kill -9 <PID>

# Option 2: Change port in config.json
nano config.json
# Change "port": 5000 to another port

# Restart service
sudo systemctl restart nvidia-gpu-benchmark
```

### 4. Service Won't Start

**Error**: Service fails to start

**Solution**:
```bash
# Check service status
sudo systemctl status nvidia-gpu-benchmark

# View detailed logs
sudo journalctl -u nvidia-gpu-benchmark -n 100 --no-pager

# Check log files
tail -n 50 /opt/nvidia-gpu-benchmark/logs/service_error.log

# Common fixes:
# 1. Verify Python virtual environment
cd /opt/nvidia-gpu-benchmark
source venv/bin/activate
python3 -c "import pynvml; pynvml.nvmlInit()"

# 2. Fix permissions
sudo chown -R $USER:$USER /opt/nvidia-gpu-benchmark

# 3. Reinstall
sudo ./uninstall.sh
sudo ./install.sh
```

### 5. No GPUs Detected in Dashboard

**Problem**: Dashboard shows "No GPUs detected"

**Solution**:
```bash
# Test nvidia-smi directly
nvidia-smi

# If nvidia-smi works, check NVML Python binding
python3 -c "import pynvml; pynvml.nvmlInit(); print(f'GPUs: {pynvml.nvmlDeviceGetCount()}'); pynvml.nvmlShutdown()"

# Check if user has access to GPU
groups $USER

# Add user to video group if needed
sudo usermod -a -G video $USER
# Log out and back in
```

### 6. Fan Control Not Working

**Problem**: Fan speed control has no effect

**Solution**:

Fan control has limitations:
- Requires specific NVIDIA driver versions
- Not all GPUs support software fan control
- May need X server running
- Some GPUs have hardware-locked fan curves

**Workarounds**:
```bash
# Check if fan control is available
nvidia-smi -q -d SUPPORTED_CLOCKS | grep -i fan

# Use nvidia-settings (requires X server)
nvidia-settings -a "[gpu:0]/GPUFanControlState=1"
nvidia-settings -a "[fan:0]/GPUTargetFanSpeed=75"

# Install CoolBits (enables overclocking/fan control)
# Edit /etc/X11/xorg.conf or /etc/X11/xorg.conf.d/20-nvidia.conf
# Add: Option "Coolbits" "4"
# Restart X server
```

### 7. Benchmark Crashes or Freezes

**Problem**: System freezes during benchmark

**Solution**:

1. **Reduce stress level**: Start with 50% instead of 100%
2. **Check temperature limits**: Lower max temp in settings
3. **Update drivers**: Ensure latest NVIDIA drivers
4. **Check power supply**: Ensure adequate PSU wattage
5. **Check for hardware issues**: Run memory test

```bash
# Check crash logs
cat /opt/nvidia-gpu-benchmark/logs/crash_detection.log

# Check system logs
dmesg | tail -n 50

# Check GPU errors
nvidia-smi -q | grep -i error
```

### 8. High Memory Usage

**Problem**: Application uses too much RAM

**Solution**:
```bash
# Reduce monitoring frequency in config.json
nano config.json
# Change "poll_interval": 0.5 to 1.0 or higher

# Reduce history size
# Change "history_size": 300 to 100

# Restart service
sudo systemctl restart nvidia-gpu-benchmark
```

### 9. Can't Access Dashboard from Another Computer

**Problem**: Can't access `http://SERVER_IP:5000`

**Solution**:
```bash
# Check if server is listening on all interfaces
sudo netstat -tulpn | grep 5000
# Should show 0.0.0.0:5000, not 127.0.0.1:5000

# Verify config.json has correct host
cat config.json | grep host
# Should be "host": "0.0.0.0"

# Check firewall
sudo ufw status
sudo ufw allow 5000/tcp

# Or disable firewall temporarily (not recommended)
sudo ufw disable
```

### 10. SSL/HTTPS Issues

**Problem**: Want to use HTTPS

**Solution**:

The default setup uses HTTP. For HTTPS:

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# Modify server.py to use SSL
# Add to the socketio.run() call:
# ssl_context=('cert.pem', 'key.pem')
```

### 11. Benchmark Results Not Saving

**Problem**: Completed benchmarks disappear

**Solution**:

Benchmark results are stored in memory by default. To persist:

```bash
# Add to config.json
"benchmark": {
  "save_results": true,
  "results_directory": "results"
}

# Create results directory
mkdir -p /opt/nvidia-gpu-benchmark/results
```

### 12. Permission Denied Errors

**Problem**: Various permission errors

**Solution**:
```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/nvidia-gpu-benchmark

# Fix file permissions
sudo chmod -R 755 /opt/nvidia-gpu-benchmark
sudo chmod +x /opt/nvidia-gpu-benchmark/*.sh
sudo chmod +x /opt/nvidia-gpu-benchmark/*.py

# Fix log directory
sudo chmod 777 /opt/nvidia-gpu-benchmark/logs
```

## Getting Help

### Check Logs

```bash
# Application logs
tail -f /opt/nvidia-gpu-benchmark/logs/server.log

# Service logs
sudo journalctl -u nvidia-gpu-benchmark -f

# Crash logs
cat /opt/nvidia-gpu-benchmark/logs/crash_detection.log

# System GPU logs
dmesg | grep -i nvidia
```

### Diagnostic Information

Run these commands when reporting issues:

```bash
# System info
./system_info.sh > diagnostic.txt

# Test results
./test.sh >> diagnostic.txt

# Service status
sudo systemctl status nvidia-gpu-benchmark >> diagnostic.txt

# Recent logs
sudo journalctl -u nvidia-gpu-benchmark -n 50 >> diagnostic.txt
```

### Hardware Checks

```bash
# GPU health check
nvidia-smi -q

# Memory test (requires GPU idle)
nvidia-smi -i 0 --test-memory=short

# Temperature monitoring
watch -n 1 nvidia-smi --query-gpu=temperature.gpu --format=csv
```

## Performance Tips

### Optimize for Speed

1. **Increase monitoring interval**: Less frequent updates
2. **Reduce history size**: Lower memory usage
3. **Use wired connection**: More stable than WiFi
4. **Close unnecessary applications**: Free up resources

### Optimize for Accuracy

1. **Lower monitoring interval**: More frequent updates (0.5s or less)
2. **Run benchmarks longer**: Better statistical data
3. **Isolate GPU**: Don't use GPU during benchmark
4. **Fixed fan speed**: Eliminate variable cooling

### Optimize for Stability

1. **Enable temperature limits**: Prevent overheating
2. **Start with low stress**: Gradually increase
3. **Monitor power draw**: Ensure PSU can handle load
4. **Good ventilation**: Keep case cool

## Advanced Configuration

### Custom Stress Levels

Edit `config.json`:
```json
"stress_levels": {
  "low": 20,
  "medium": 50,
  "high": 75,
  "extreme": 100
}
```

### Temperature Thresholds

```json
"safety": {
  "max_temperature": 80,
  "critical_temperature": 85,
  "auto_shutdown_on_critical": true
}
```

### Monitoring Settings

```json
"monitoring": {
  "poll_interval": 0.5,
  "history_size": 300
}
```

## Still Having Issues?

1. Check README.md for detailed documentation
2. Run `./test.sh` to diagnose problems
3. Review all log files in `logs/` directory
4. Ensure NVIDIA drivers are up to date
5. Test with minimal configuration first
