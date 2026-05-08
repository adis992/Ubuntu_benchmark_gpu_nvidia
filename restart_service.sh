#!/bin/bash

# Restart NVIDIA GPU Benchmark Service
# Use this after making changes to apply updates

SERVICE_NAME="nvidia-gpu-benchmark"

echo "================================================"
echo "🔄 Restarting NVIDIA GPU Benchmark Service"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check if service exists
if ! systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
    echo "❌ Service not installed."
    echo ""
    echo "Install with: sudo ./install.sh"
    exit 1
fi

echo "✓ Service found"

# Copy updated files to installation directory (if running from source)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/nvidia-gpu-benchmark"

if [ "$SCRIPT_DIR" != "$INSTALL_DIR" ] && [ -d "$INSTALL_DIR" ]; then
    echo ""
    echo "📁 Copying updated files to installation directory..."
    
    # Copy Python files
    cp -f "$SCRIPT_DIR"/*.py "$INSTALL_DIR/" 2>/dev/null
    
    # Copy config
    cp -f "$SCRIPT_DIR"/config.json "$INSTALL_DIR/" 2>/dev/null
    
    # Copy web files
    cp -rf "$SCRIPT_DIR"/templates "$INSTALL_DIR/" 2>/dev/null
    cp -rf "$SCRIPT_DIR"/static "$INSTALL_DIR/" 2>/dev/null
    
    echo "✓ Files updated"
fi

# Always update the service file to ensure correct settings (no NVML-blocking security options)
echo ""
echo "🔧 Updating service file..."
SERVICE_USER_ACTUAL=$(stat -c '%U' "$INSTALL_DIR" 2>/dev/null || echo "noname")
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << SVCEOF
[Unit]
Description=NVIDIA GPU Benchmark Tool
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="HOME=/root"
ExecStart=${INSTALL_DIR}/venv/bin/python3 ${INSTALL_DIR}/server.py
Restart=on-failure
RestartSec=10
StandardOutput=append:${INSTALL_DIR}/logs/service.log
StandardError=append:${INSTALL_DIR}/logs/service_error.log

[Install]
WantedBy=multi-user.target
SVCEOF
systemctl daemon-reload
echo "✓ Service file updated"

# Stop service
echo ""
echo "⏹️  Stopping service..."
systemctl stop "$SERVICE_NAME"

if [ $? -eq 0 ]; then
    echo "✓ Service stopped"
else
    echo "⚠️  Service may not be running"
fi

# Wait a moment
sleep 2

# Start service
echo ""
echo "▶️  Starting service..."
systemctl start "$SERVICE_NAME"

if [ $? -eq 0 ]; then
    echo "✓ Service started"
else
    echo "❌ Failed to start service"
    echo ""
    echo "Check logs:"
    echo "  sudo journalctl -u $SERVICE_NAME -n 50"
    exit 1
fi

# Wait for service to initialize
sleep 3

# Check status
echo ""
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "================================================"
    echo "✅ Service restarted successfully!"
    echo "================================================"
    echo ""
    echo "Service Status: ✓ Running"
    echo "Dashboard URL:  http://localhost:5000"
    echo "                http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo "View logs:"
    echo "  sudo journalctl -u $SERVICE_NAME -f"
    echo ""
else
    echo "================================================"
    echo "⚠️ Service is not running"
    echo "================================================"
    echo ""
    echo "Check status: sudo systemctl status $SERVICE_NAME"
    echo "View logs:    sudo journalctl -u $SERVICE_NAME -n 50"
    echo ""
    exit 1
fi
