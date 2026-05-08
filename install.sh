#!/bin/bash

# NVIDIA GPU Benchmark Tool - Installation Script
# This script will install and setup the GPU benchmark tool as a system service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="nvidia-gpu-benchmark"
SERVICE_USER="root"
INSTALL_DIR="/opt/nvidia-gpu-benchmark"

echo "================================================"
echo "NVIDIA GPU Benchmark Tool - Installation"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "✓ Running with root privileges"

# Check for NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ nvidia-smi not found. Please install NVIDIA drivers first."
    exit 1
fi

echo "✓ NVIDIA drivers detected"

# Kill any existing servers before starting
echo ""
echo "🔪 Stopping any running servers..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
pkill -9 -f "python3.*server.py" 2>/dev/null || true
pkill -9 -f "server.py" 2>/dev/null || true
sleep 2
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 5001/tcp 2>/dev/null || true
sleep 2
echo "✓ Ports 5000/5001 cleared"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Python ${PYTHON_VERSION} detected"

# Install system dependencies
echo ""
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y python3-pip python3-venv python3-dev build-essential

# Create installation directory
echo ""
echo "📁 Creating installation directory..."
mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
cd "$INSTALL_DIR"

echo "✓ Files copied to $INSTALL_DIR"

# Create virtual environment
echo ""
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "✓ Virtual environment created"

# Install Python dependencies
echo ""
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Python dependencies installed"

# Install CuPy for GPU stress testing
echo ""
echo "🚀 Installing CuPy (GPU stress testing library)..."
CUDA_VER=$(nvidia-smi | grep -oP 'CUDA Version: \K[0-9]+' | head -1)
echo "   Detected CUDA major version: $CUDA_VER"
if pip install cupy-cuda12x -q 2>/dev/null; then
    echo "✓ CuPy installed (cuda12x)"
elif pip install cupy-cuda11x -q 2>/dev/null; then
    echo "✓ CuPy installed (cuda11x)"
else
    echo "⚠️  CuPy not installed (GPU stress will use CPU fallback)"
    echo "   Manual install: pip install cupy-cuda12x"
fi

# Create logs directory
mkdir -p logs

# Set permissions
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/start.sh"

echo "✓ Permissions set"

# Create systemd service
echo ""
echo "⚙️ Creating systemd service..."

cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=NVIDIA GPU Benchmark Tool
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="HOME=/root"
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/server.py
Restart=on-failure
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/service.log
StandardError=append:$INSTALL_DIR/logs/service_error.log

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Systemd service created"

# Reload systemd
echo ""
echo "🔄 Reloading systemd..."
systemctl daemon-reload

echo "✓ Systemd reloaded"

# Enable service
echo ""
echo "🚀 Enabling service to start on boot..."
systemctl enable "$SERVICE_NAME"

echo "✓ Service enabled"

# Start service
echo ""
echo "▶️ Starting service..."
systemctl start "$SERVICE_NAME"

echo "✓ Service started"

# Wait a moment for service to start
sleep 3

# Check service status
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo ""
    echo "================================================"
    echo "✅ Installation completed successfully!"
    echo "================================================"
    echo ""
    echo "Service Status: $(systemctl is-active $SERVICE_NAME)"
    echo "Dashboard URL: http://localhost:5000  (samo ovaj port!)"
    echo ""
    echo "Useful commands:"
    echo "  Start service:   sudo systemctl start $SERVICE_NAME"
    echo "  Stop service:    sudo systemctl stop $SERVICE_NAME"
    echo "  Restart service: sudo systemctl restart $SERVICE_NAME"
    echo "  View status:     sudo systemctl status $SERVICE_NAME"
    echo "  View logs:       sudo journalctl -u $SERVICE_NAME -f"
    echo "  Manual start:    cd $INSTALL_DIR && ./start.sh"
    echo ""
    echo "The dashboard should now be accessible at:"
    echo "  http://localhost:5000"
    echo "  http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
else
    echo ""
    echo "⚠️ Service failed to start. Checking logs..."
    echo ""
    journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    echo ""
    echo "Please check the logs above for errors."
    exit 1
fi
