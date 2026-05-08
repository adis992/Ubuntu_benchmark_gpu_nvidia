# 📦 Project Structure

```
Ubuntu_benchmark_gpu_nvidia/
│
├── 📄 Core Application Files
│   ├── server.py              # Flask server with REST API & WebSocket
│   ├── gpu_monitor.py         # NVIDIA GPU monitoring (pynvml wrapper)
│   ├── benchmark.py           # Benchmark workload & crash detection
│   └── gpu_stress.py          # Standalone GPU stress test utility
│
├── ⚙️ Configuration
│   ├── config.json            # Main configuration file
│   └── requirements.txt       # Python dependencies
│
├── 🌐 Web Interface
│   ├── templates/
│   │   └── index.html         # Main dashboard HTML
│   └── static/
│       ├── css/
│       │   └── style.css      # Dashboard styles
│       └── js/
│           └── app.js         # Frontend JavaScript (WebSocket, API calls)
│
├── 🚀 Installation & Management
│   ├── install.sh             # Automated installation script
│   ├── uninstall.sh           # Removal script
│   ├── start.sh               # Manual start script
│   ├── test.sh                # System check & validation
│   ├── monitor.sh             # Terminal-based GPU monitor
│   └── system_info.sh         # System information display
│
├── 📚 Documentation
│   ├── README.md              # Comprehensive documentation
│   ├── QUICKSTART.md          # Quick start guide
│   ├── TROUBLESHOOTING.md     # Troubleshooting guide
│   ├── PROJECT_STRUCTURE.md   # This file
│   └── LICENSE                # MIT License
│
├── 📁 Generated Directories
│   ├── logs/                  # Application & system logs
│   │   ├── server.log         # Main server log
│   │   ├── service.log        # Systemd service output
│   │   ├── service_error.log  # Systemd error output
│   │   └── crash_detection.log # Critical events log
│   └── venv/                  # Python virtual environment (after install)
│
└── 🗑️ Ignored Files
    ├── .gitignore             # Git ignore rules
    └── __pycache__/           # Python cache files

```

## File Descriptions

### Core Application

**server.py** (277 lines)
- Main Flask application
- REST API endpoints
- WebSocket server for real-time updates
- Background monitoring thread
- Configuration management

**gpu_monitor.py** (195 lines)
- NVML (NVIDIA Management Library) wrapper
- GPU detection and initialization
- Real-time metrics collection
- Fan control interface
- Thermal safety checks

**benchmark.py** (292 lines)
- Benchmark workload management
- Multi-GPU stress testing
- Crash detection system
- Signal handling
- Process management

**gpu_stress.py** (230 lines)
- Standalone stress test tool
- CuPy-based GPU computation
- Command-line interface
- Graceful shutdown handling

### Configuration

**config.json**
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  },
  "benchmark": {
    "default_duration": 300,
    "max_duration": 86400,
    "stress_levels": {...}
  },
  "monitoring": {
    "poll_interval": 0.5,
    "history_size": 300
  },
  "safety": {
    "max_temperature": 85,
    "critical_temperature": 90,
    "auto_shutdown_on_critical": true
  }
}
```

**requirements.txt**
- flask: Web framework
- flask-cors: Cross-origin support
- flask-socketio: WebSocket support
- nvidia-ml-py: NVIDIA GPU management
- psutil: System monitoring
- eventlet: Async server

### Web Interface

**templates/index.html** (115 lines)
- Modern, responsive dashboard
- GPU selection controls
- Benchmark configuration
- Safety settings
- Real-time monitoring display
- Active benchmarks list
- System logs

**static/css/style.css** (500+ lines)
- Dark theme design
- Responsive grid layouts
- Animated indicators
- Color-coded warnings
- Professional styling
- Mobile-friendly

**static/js/app.js** (450+ lines)
- WebSocket client
- Real-time data updates
- API integration
- Dynamic UI updates
- Event handling
- Chart updates (if enabled)

### Installation Scripts

**install.sh** (150+ lines)
```bash
# - Check system requirements
# - Install dependencies
# - Create virtual environment
# - Install Python packages
# - Create systemd service
# - Start service automatically
```

**uninstall.sh** (70+ lines)
```bash
# - Stop service
# - Disable service
# - Remove service file
# - Optional: remove installation directory
```

**start.sh** (50+ lines)
```bash
# - Check prerequisites
# - Activate virtual environment
# - Display GPU information
# - Start server manually
```

### Utility Scripts

**test.sh** (120+ lines)
- System requirements check
- Dependency verification
- Service status check
- Port availability check
- GPU monitoring test
- Diagnostic summary

**monitor.sh** (140+ lines)
- Terminal-based monitoring
- Color-coded status
- Real-time updates
- Temperature alerts
- System load display
- Continuous refresh

**system_info.sh** (80+ lines)
- System information
- CPU details
- Memory usage
- GPU information
- Network configuration
- Service status

## Dependencies

### System
- Ubuntu 20.04+ or Debian-based Linux
- NVIDIA GPU with compatible drivers
- Python 3.8+
- Build tools (gcc, make)

### Python Packages
- flask (3.0.0)
- flask-cors (4.0.0)
- flask-socketio (5.3.5)
- nvidia-ml-py (12.535.133)
- psutil (5.9.6)
- python-socketio (5.10.0)
- eventlet (0.33.3)

### Optional
- cupy (for advanced GPU stress testing)
- numpy (for numerical operations)

## Installation Structure

After running `./install.sh`, files are copied to:

```
/opt/nvidia-gpu-benchmark/
├── All project files
├── venv/ (Python virtual environment)
└── logs/ (Runtime logs)

/etc/systemd/system/
└── nvidia-gpu-benchmark.service
```

## Runtime Flow

```
1. Systemd starts service
   ↓
2. server.py initializes
   ↓
3. gpu_monitor.py detects GPUs
   ↓
4. Flask server starts on port 5000
   ↓
5. WebSocket server starts
   ↓
6. Monitoring thread begins
   ↓
7. Dashboard accessible at http://localhost:5000
   ↓
8. User starts benchmark
   ↓
9. benchmark.py creates stress processes
   ↓
10. Real-time metrics sent via WebSocket
    ↓
11. Safety checks monitor temperature
    ↓
12. Benchmark completes or is stopped
    ↓
13. Results logged
```

## API Endpoints

### REST API
```
GET  /                          Dashboard HTML
GET  /api/status               System status
GET  /api/gpus                 All GPU information
GET  /api/gpu/<id>             Specific GPU details
POST /api/benchmark/start      Start benchmark
POST /api/benchmark/stop/<id>  Stop benchmark
GET  /api/benchmarks/active    Active benchmarks
GET  /api/benchmarks/results   Benchmark results
POST /api/fan/set              Set fan speed
POST /api/fan/reset            Reset fan control
GET  /api/config               Get configuration
POST /api/config/update        Update configuration
```

### WebSocket Events
```
connect                Client connects
disconnect             Client disconnects
start_monitoring       Begin real-time updates
stop_monitoring        Stop real-time updates
gpu_update            Server broadcasts GPU data
monitoring_status     Monitoring state change
```

## Log Files

**server.log**
- Application startup/shutdown
- API requests
- Benchmark events
- Configuration changes

**crash_detection.log**
- Critical temperature events
- Unexpected process terminations
- Signal handling
- Emergency shutdowns

**service.log**
- Systemd service output
- Standard output messages

**service_error.log**
- Python exceptions
- Error tracebacks
- Fatal errors

## Data Flow

```
NVIDIA GPU → nvidia-smi/NVML → gpu_monitor.py → server.py → WebSocket → Dashboard
                                       ↓
                                 benchmark.py → GPU stress processes
                                       ↓
                                   logs/*.log
```

## Security Considerations

- **No authentication**: Add authentication for production
- **HTTP only**: Use HTTPS for remote access
- **Root privileges**: Required for fan control (limited)
- **Port exposure**: Firewall configuration recommended
- **Input validation**: All user inputs validated
- **Process isolation**: Benchmarks run in separate processes

## Scalability

- **Multi-GPU**: Supports unlimited GPUs
- **Concurrent benchmarks**: Multiple benchmarks possible
- **WebSocket broadcasting**: All clients receive updates
- **History size**: Configurable (trade-off: memory vs history)
- **Log rotation**: Manual rotation recommended

## Future Enhancements

- [ ] Database storage for historical data
- [ ] User authentication system
- [ ] Email/webhook notifications
- [ ] Custom CUDA kernels
- [ ] Benchmark result comparison
- [ ] API rate limiting
- [ ] HTTPS support
- [ ] Docker containerization
- [ ] Multi-machine monitoring
- [ ] Mobile app

## Contributing

To extend this project:

1. **Add new metrics**: Modify `gpu_monitor.py`
2. **New API endpoints**: Add to `server.py`
3. **UI improvements**: Edit `templates/index.html` and `static/`
4. **New benchmarks**: Extend `benchmark.py`
5. **Additional scripts**: Add to root directory

## Performance Notes

- **WebSocket overhead**: ~1-5% CPU for real-time updates
- **Monitoring impact**: <1% GPU overhead
- **Memory usage**: ~50-100MB base + history
- **Network bandwidth**: ~1-2 KB/s per client for updates

---

This structure provides a complete, professional GPU benchmarking solution with emphasis on usability, safety, and extensibility.
