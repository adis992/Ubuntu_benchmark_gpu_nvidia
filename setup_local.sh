#!/bin/bash

# Local Setup Script
# Installs dependencies locally without requiring root or system installation
# Use this for testing or development

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================"
echo "NVIDIA GPU Benchmark Tool - Local Setup"
echo "================================================"
echo ""

# Check for NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ nvidia-smi not found. Please install NVIDIA drivers first."
    exit 1
fi

echo "✓ NVIDIA drivers detected"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Python ${PYTHON_VERSION} detected"

cd "$SCRIPT_DIR"

# Create virtual environment
echo ""
echo "🐍 Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

echo "✓ Virtual environment created"

# Install Python dependencies
echo ""
echo "📚 Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt

echo "✓ Python dependencies installed"

# Create logs directory
mkdir -p logs

echo "✓ Logs directory created"

echo ""
echo "================================================"
echo "✅ Local setup completed successfully!"
echo "================================================"
echo ""
echo "To start the application:"
echo "  ./start.sh"
echo ""
echo "Dashboard will be available at:"
echo "  http://localhost:5000"
echo ""
echo "Note: This is a local installation."
echo "For system-wide installation with auto-start, run:"
echo "  sudo ./install.sh"
echo ""
