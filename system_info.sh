#!/bin/bash

# System Information Script
# Displays comprehensive system and GPU information

echo "================================================"
echo "🖥️  SYSTEM INFORMATION"
echo "================================================"
echo ""

# System Info
echo "📋 System:"
echo "  OS:          $(lsb_release -d | cut -f2)"
echo "  Kernel:      $(uname -r)"
echo "  Hostname:    $(hostname)"
echo "  Uptime:      $(uptime -p)"
echo ""

# CPU Info
echo "💻 CPU:"
cpu_model=$(lscpu | grep "Model name" | cut -d: -f2 | xargs)
cpu_cores=$(nproc)
echo "  Model:       $cpu_model"
echo "  Cores:       $cpu_cores"
echo ""

# Memory Info
echo "🧠 Memory:"
free -h | awk 'NR==2 {printf "  Total:       %s\n  Used:        %s\n  Available:   %s\n", $2, $3, $7}'
echo ""

# NVIDIA Driver Info
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 NVIDIA Driver:"
    driver_version=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -n1)
    cuda_version=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
    echo "  Driver:      $driver_version"
    echo "  CUDA:        $cuda_version"
    echo ""
    
    echo "📊 GPU Information:"
    nvidia-smi --query-gpu=index,name,pci.bus_id,memory.total --format=csv,noheader | \
        awk -F', ' '{printf "  GPU %s: %s\n    PCI:    %s\n    Memory: %s\n\n", $1, $2, $3, $4}'
    
    echo "🌡️  Current GPU Status:"
    nvidia-smi --query-gpu=index,temperature.gpu,utilization.gpu,utilization.memory,power.draw,fan.speed --format=csv | \
        column -t -s ','
    echo ""
else
    echo "❌ NVIDIA drivers not found"
    echo ""
fi

# Disk Info
echo "💾 Disk Usage:"
df -h / | awk 'NR==2 {printf "  Root:        %s / %s (%s used)\n", $3, $2, $5}'
echo ""

# Network Info
echo "🌐 Network:"
ip_address=$(hostname -I | awk '{print $1}')
echo "  IP Address:  $ip_address"
echo ""

# Check if service is running
if systemctl is-active --quiet nvidia-gpu-benchmark 2>/dev/null; then
    echo "🚀 Service Status: ✅ Running"
    echo "   Dashboard:    http://localhost:5000"
    echo "                 http://$ip_address:5000"
else
    echo "🚀 Service Status: ⛔ Not Running"
    echo "   Start with:   sudo systemctl start nvidia-gpu-benchmark"
fi

echo ""
echo "================================================"
