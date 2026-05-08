#!/bin/bash

# Quick GPU Stress Test
# Tests if CuPy is working properly

echo "================================================"
echo "🧪 Testing GPU Stress Capability"
echo "================================================"
echo ""

# Check if CuPy is installed
if /opt/nvidia-gpu-benchmark/venv/bin/python3 -c "import cupy" 2>/dev/null; then
    echo "✅ CuPy is installed"
    echo ""
    echo "Testing GPU stress on GPU 0 for 10 seconds..."
    echo ""
    
    /opt/nvidia-gpu-benchmark/venv/bin/python3 gpu_stress.py -g 0 -s 100 &
    STRESS_PID=$!
    
    sleep 3
    
    echo ""
    echo "📊 GPU Status:"
    nvidia-smi --query-gpu=index,utilization.gpu,temperature.gpu,power.draw --format=csv,noheader,nounits
    
    sleep 7
    
    kill $STRESS_PID 2>/dev/null
    
    echo ""
    echo "✅ Test complete!"
else
    echo "❌ CuPy is NOT installed"
    echo ""
    echo "Install with:"
    echo "  sudo ./install_cupy.sh"
    echo ""
    exit 1
fi
