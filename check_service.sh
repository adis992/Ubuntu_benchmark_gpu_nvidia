#!/bin/bash

# Check Service Status Script
# Quick check of the NVIDIA GPU Benchmark service

SERVICE_NAME="nvidia-gpu-benchmark"
INSTALL_DIR="/opt/nvidia-gpu-benchmark"

echo "================================================"
echo "📊 NVIDIA GPU Benchmark Service Status"
echo "================================================"
echo ""

# Check if service exists
if ! systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
    echo "❌ Service not installed"
    echo ""
    echo "Install with: sudo ./install.sh"
    exit 1
fi

# Get service status
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "Status: ✅ RUNNING"
else
    echo "Status: ⛔ STOPPED"
fi

echo ""

# Show detailed status
systemctl status "$SERVICE_NAME" --no-pager -l | head -n 15

echo ""
echo "================================================"

# Show URLs if running
if systemctl is-active --quiet "$SERVICE_NAME"; then
    PORT=$(grep -oP '"port":\s*\K\d+' "$INSTALL_DIR/config.json" 2>/dev/null || echo "5001")
    IP=$(hostname -I | awk '{print $1}')
    
    echo "🌐 Dashboard URLs:"
    echo "   http://localhost:$PORT"
    echo "   http://$IP:$PORT"
    echo ""
    echo "📝 View logs:"
    echo "   sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "🔄 Restart service:"
    echo "   sudo ./restart_service.sh"
else
    echo "⚠️  Service is not running"
    echo ""
    echo "Start with:"
    echo "   sudo systemctl start $SERVICE_NAME"
    echo ""
    echo "Or restart with:"
    echo "   sudo ./restart_service.sh"
fi

echo "================================================"
