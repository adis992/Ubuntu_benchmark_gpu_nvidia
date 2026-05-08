#!/bin/bash

# Fix Systemd Service Script
# Fixes the systemd service configuration for already installed instances

set -e

SERVICE_NAME="nvidia-gpu-benchmark"
INSTALL_DIR="/opt/nvidia-gpu-benchmark"

echo "================================================"
echo "NVIDIA GPU Benchmark Service - Fix Script"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check if service exists
if [ ! -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    echo "❌ Service not installed. Run ./install.sh first."
    exit 1
fi

echo "✓ Service file found"

# Check if installation directory exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ Installation directory not found at $INSTALL_DIR"
    exit 1
fi

echo "✓ Installation directory found"

# Stop service if running
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "⏹️  Stopping service..."
    systemctl stop "$SERVICE_NAME"
    echo "✓ Service stopped"
fi

# Get service user
SERVICE_USER=$(grep "^User=" "/etc/systemd/system/${SERVICE_NAME}.service" | cut -d= -f2)
if [ -z "$SERVICE_USER" ]; then
    SERVICE_USER="${SUDO_USER:-$USER}"
fi

echo "✓ Service user: $SERVICE_USER"

# Recreate systemd service with proper configuration
echo ""
echo "⚙️  Updating systemd service..."

cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=NVIDIA GPU Benchmark Tool
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="VIRTUAL_ENV=$INSTALL_DIR/venv"
ExecStart=/bin/bash -c 'source $INSTALL_DIR/venv/bin/activate && python3 $INSTALL_DIR/server.py'
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/service.log
StandardError=append:$INSTALL_DIR/logs/service_error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Service file updated"

# Reload systemd
echo ""
echo "🔄 Reloading systemd..."
systemctl daemon-reload

echo "✓ Systemd reloaded"

# Start service
echo ""
echo "▶️  Starting service..."
systemctl start "$SERVICE_NAME"

echo "✓ Service started"

# Wait a moment for service to start
sleep 3

# Check service status
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo ""
    echo "================================================"
    echo "✅ Service fixed and running!"
    echo "================================================"
    echo ""
    echo "Service Status: $(systemctl is-active $SERVICE_NAME)"
    echo "Dashboard URL: http://localhost:5000"
    echo ""
    echo "View logs:"
    echo "  sudo journalctl -u $SERVICE_NAME -f"
    echo "  tail -f $INSTALL_DIR/logs/service.log"
    echo ""
else
    echo ""
    echo "⚠️ Service still having issues. Checking logs..."
    echo ""
    journalctl -u "$SERVICE_NAME" -n 30 --no-pager
    echo ""
    echo "Also check:"
    echo "  cat $INSTALL_DIR/logs/service_error.log"
    echo ""
    exit 1
fi
