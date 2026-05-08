#!/bin/bash

# Quick Test Script
# Performs a basic functionality test of the GPU benchmark tool

echo "================================================"
echo "🧪 NVIDIA GPU Benchmark Tool - Quick Test"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check NVIDIA drivers
echo "1️⃣  Checking NVIDIA drivers..."
if command -v nvidia-smi &> /dev/null; then
    echo "   ✅ nvidia-smi found"
    nvidia-smi --query-gpu=count --format=csv,noheader | head -n1 | xargs echo "   GPUs detected:"
else
    echo "   ❌ nvidia-smi not found"
    exit 1
fi
echo ""

# Check Python
echo "2️⃣  Checking Python..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    echo "   ✅ $python_version"
else
    echo "   ❌ Python 3 not found"
    exit 1
fi
echo ""

# Check if installed as service
echo "3️⃣  Checking service installation..."
if systemctl list-unit-files | grep -q nvidia-gpu-benchmark; then
    echo "   ✅ Service installed"
    if systemctl is-active --quiet nvidia-gpu-benchmark; then
        echo "   ✅ Service is running"
    else
        echo "   ⚠️  Service is not running"
        echo "   Start with: sudo systemctl start nvidia-gpu-benchmark"
    fi
else
    echo "   ⚠️  Service not installed"
    echo "   Install with: sudo ./install.sh"
fi
echo ""

# Check Python dependencies
echo "4️⃣  Checking Python dependencies..."
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   ✅ Virtual environment found"
else
    echo "   ⚠️  Virtual environment not found"
fi

missing_deps=0
while IFS= read -r package; do
    pkg_name=$(echo "$package" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1)
    if python3 -c "import $pkg_name" 2>/dev/null; then
        echo "   ✅ $pkg_name"
    else
        echo "   ❌ $pkg_name (missing)"
        missing_deps=$((missing_deps + 1))
    fi
done < <(grep -v "^#" requirements.txt | grep -v "^$" | head -n 7)

if [ $missing_deps -gt 0 ]; then
    echo ""
    echo "   ⚠️  Missing dependencies. Install with:"
    echo "   pip install -r requirements.txt"
fi
echo ""

# Check port availability
echo "5️⃣  Checking port 5000..."
if netstat -tuln 2>/dev/null | grep -q ":5000 " || ss -tuln 2>/dev/null | grep -q ":5000 "; then
    echo "   ⚠️  Port 5000 is in use"
    echo "   Service might be running, or another application is using the port"
else
    echo "   ✅ Port 5000 is available"
fi
echo ""

# Test GPU monitoring
echo "6️⃣  Testing GPU monitoring..."
if python3 -c "import pynvml; pynvml.nvmlInit(); print('   ✅ GPU monitoring works'); pynvml.nvmlShutdown()" 2>/dev/null; then
    true
else
    echo "   ❌ GPU monitoring failed"
    echo "   Make sure pynvml is installed: pip install nvidia-ml-py"
fi
echo ""

# Summary
echo "================================================"
echo "📊 Test Summary"
echo "================================================"
echo ""

if [ $missing_deps -eq 0 ]; then
    echo "✅ All dependencies are installed"
    echo ""
    echo "To start the benchmark tool:"
    echo "  Manual:  ./start.sh"
    echo "  Service: sudo systemctl start nvidia-gpu-benchmark"
    echo ""
    echo "Dashboard will be available at:"
    echo "  http://localhost:5000"
else
    echo "⚠️  Some dependencies are missing"
    echo ""
    echo "Please install missing dependencies:"
    echo "  pip install -r requirements.txt"
    echo ""
    echo "Or run the full installation:"
    echo "  sudo ./install.sh"
fi

echo ""
echo "================================================"
