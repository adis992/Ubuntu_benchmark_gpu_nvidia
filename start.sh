#!/bin/bash

# NVIDIA GPU Benchmark Tool - Manual Start Script
# Use this to start the application manually without using the systemd service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================"
echo "NVIDIA GPU Benchmark Tool - Manual Start"
echo "================================================"
echo ""

# Check if running from installation directory
if [ ! -f "$SCRIPT_DIR/server.py" ]; then
    echo "❌ server.py not found in current directory"
    echo "Please run this script from the installation directory"
    exit 1
fi

# Check for NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ nvidia-smi not found. Please install NVIDIA drivers first."
    exit 1
fi

echo "✓ NVIDIA drivers detected"

# Check if running from installation directory or source directory
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "✓ Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
elif [ -d "/opt/nvidia-gpu-benchmark/venv" ]; then
    echo "✓ Using installed virtual environment..."
    source "/opt/nvidia-gpu-benchmark/venv/bin/activate"
else
    echo "⚠️ Virtual environment not found."
    echo "Creating local virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
    source "$SCRIPT_DIR/venv/bin/activate"
    echo "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r "$SCRIPT_DIR/requirements.txt"
    echo "✓ Dependencies installed"
fi

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Display GPU information
echo ""
echo "🎮 Detected GPUs:"
nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu --format=csv,noheader | \
    awk -F', ' '{printf "  GPU %s: %s (Temp: %s°C, Util: %s)\n", $1, $2, $3, $4}'

echo ""
echo "================================================"
echo "Starting server..."
echo "================================================"
echo ""
echo "Dashboard will be available at:"
echo "  http://localhost:5000"
echo "  http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo "YOUR_IP"):5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
cd "$SCRIPT_DIR"
python3 server.py
