#!/bin/bash

# Install CuPy for GPU Stress Testing
# Run with: sudo ./install_cupy.sh

echo "================================================"
echo "🚀 Installing CuPy for GPU Stress Testing"
echo "================================================"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo ./install_cupy.sh"
    exit 1
fi

echo "📋 Checking CUDA version..."
CUDA_VERSION=$(nvidia-smi | grep -oP 'CUDA Version: \K[0-9.]+' | head -1)
echo "✓ Found CUDA $CUDA_VERSION"
echo ""

# Install in service venv
if [ -d "/opt/nvidia-gpu-benchmark/venv" ]; then
    echo "📦 Installing CuPy in service venv..."
    /opt/nvidia-gpu-benchmark/venv/bin/pip install cupy-cuda12x
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ CuPy installed successfully in service!"
        echo ""
        echo "🔄 Restart the service to use it:"
        echo "   sudo ./restart_service.sh"
        echo ""
    else
        echo "❌ Installation failed"
        exit 1
    fi
else
    echo "⚠️  Service not installed at /opt/nvidia-gpu-benchmark"
    echo ""
    echo "Run: sudo ./install.sh first"
    exit 1
fi

# Also try to install in local venv if it exists
if [ -d "venv" ]; then
    echo "📦 Also installing in local venv..."
    # Fix ownership first
    chown -R $SUDO_USER:$SUDO_USER venv/
    sudo -u $SUDO_USER venv/bin/pip install cupy-cuda12x -q
fi

echo ""
echo "================================================"
echo "✅ Done!"
echo "================================================"
echo ""
echo "Test CuPy:"
echo "  /opt/nvidia-gpu-benchmark/venv/bin/python3 -c 'import cupy; print(\"CuPy OK!\")'"
echo ""
echo "Restart service:"
echo "  sudo ./restart_service.sh"
echo ""
