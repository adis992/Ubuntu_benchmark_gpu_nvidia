#!/bin/bash

# Quick Commands Reference
# Shows all available commands for managing the GPU Benchmark Tool

echo "================================================"
echo "🎮 NVIDIA GPU Benchmark Tool - Commands"
echo "================================================"
echo ""

echo "📦 INSTALLATION:"
echo "  sudo ./install.sh          - Install as system service (auto-start)"
echo "  ./setup_local.sh           - Local setup (no service, for testing)"
echo ""

echo "🚀 STARTING:"
echo "  ./start.sh                 - Start manually (no service)"
echo "  sudo systemctl start nvidia-gpu-benchmark"
echo "                             - Start service"
echo ""

echo "⏹️  STOPPING:"
echo "  Ctrl+C                     - Stop manual server"
echo "  sudo systemctl stop nvidia-gpu-benchmark"
echo "                             - Stop service"
echo ""

echo "🔄 RESTART (after changes):"
echo "  sudo ./restart_service.sh  - Restart service & update files"
echo "  sudo systemctl restart nvidia-gpu-benchmark"
echo "                             - Restart service only"
echo ""

echo "📊 STATUS & INFO:"
echo "  ./check_service.sh         - Check service status"
echo "  sudo systemctl status nvidia-gpu-benchmark"
echo "                             - Detailed service status"
echo "  ./system_info.sh           - System & GPU information"
echo "  ./test.sh                  - Run system tests"
echo ""

echo "📝 LOGS:"
echo "  sudo journalctl -u nvidia-gpu-benchmark -f"
echo "                             - Follow service logs"
echo "  tail -f /opt/nvidia-gpu-benchmark/logs/service.log"
echo "                             - Follow application logs"
echo "  cat logs/crash_detection.log"
echo "                             - View crash logs"
echo ""

echo "🔧 MAINTENANCE:"
echo "  sudo ./fix_service.sh      - Fix service configuration"
echo "  sudo systemctl enable nvidia-gpu-benchmark"
echo "                             - Enable auto-start on boot"
echo "  sudo systemctl disable nvidia-gpu-benchmark"
echo "                             - Disable auto-start"
echo ""

echo "🗑️  UNINSTALL:"
echo "  sudo ./uninstall.sh        - Remove service & files"
echo ""

echo "🖥️  MONITORING:"
echo "  ./monitor.sh               - Terminal GPU monitor"
echo "  nvidia-smi                 - NVIDIA System Management Interface"
echo ""

echo "🌐 WEB DASHBOARD:"
if systemctl is-active --quiet nvidia-gpu-benchmark 2>/dev/null; then
    PORT=$(grep -oP '"port":\s*\K\d+' /opt/nvidia-gpu-benchmark/config.json 2>/dev/null || echo "5001")
    IP=$(hostname -I | awk '{print $1}')
    echo "  ✅ Running at:"
    echo "     http://localhost:$PORT"
    echo "     http://$IP:$PORT"
else
    echo "  ⛔ Service not running"
    echo "     Start with: sudo systemctl start nvidia-gpu-benchmark"
fi

echo ""
echo "================================================"
echo ""
echo "📚 Full documentation: README.md"
echo "❓ Troubleshooting: TROUBLESHOOTING.md"
echo "🚀 Quick start: QUICKSTART.md"
echo ""
