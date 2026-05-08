#!/bin/bash

# Advanced GPU Monitoring Script
# Continuous monitoring of NVIDIA GPUs with alerts

ALERT_TEMP=80
CRITICAL_TEMP=85
REFRESH_INTERVAL=2

echo "================================================"
echo "🎮 Advanced GPU Monitor"
echo "================================================"
echo ""
echo "Alert temperature: ${ALERT_TEMP}°C"
echo "Critical temperature: ${CRITICAL_TEMP}°C"
echo "Refresh interval: ${REFRESH_INTERVAL}s"
echo ""
echo "Press Ctrl+C to stop"
echo "================================================"
echo ""

# Function to display colored temperature
color_temp() {
    temp=$1
    if [ $temp -ge $CRITICAL_TEMP ]; then
        echo -e "\033[1;31m${temp}°C\033[0m"  # Red
    elif [ $temp -ge $ALERT_TEMP ]; then
        echo -e "\033[1;33m${temp}°C\033[0m"  # Yellow
    else
        echo -e "\033[1;32m${temp}°C\033[0m"  # Green
    fi
}

# Function to display colored utilization
color_util() {
    util=$1
    if [ $util -ge 90 ]; then
        echo -e "\033[1;31m${util}%\033[0m"   # Red
    elif [ $util -ge 70 ]; then
        echo -e "\033[1;33m${util}%\033[0m"   # Yellow
    else
        echo -e "\033[1;32m${util}%\033[0m"   # Green
    fi
}

# Main monitoring loop
while true; do
    clear
    echo "================================================"
    echo "🎮 GPU Monitor - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "================================================"
    echo ""
    
    # Check if nvidia-smi is available
    if ! command -v nvidia-smi &> /dev/null; then
        echo "❌ nvidia-smi not found"
        exit 1
    fi
    
    # Get GPU count
    gpu_count=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -n1)
    
    # Monitor each GPU
    for (( i=0; i<$gpu_count; i++ )); do
        # Query GPU information
        gpu_info=$(nvidia-smi -i $i --query-gpu=name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw,fan.speed,clocks.gr,clocks.mem --format=csv,noheader,nounits)
        
        # Parse information
        IFS=',' read -r name temp gpu_util mem_util mem_used mem_total power fan clock_gpu clock_mem <<< "$gpu_info"
        
        # Trim whitespace
        name=$(echo "$name" | xargs)
        temp=$(echo "$temp" | xargs)
        gpu_util=$(echo "$gpu_util" | xargs)
        mem_util=$(echo "$mem_util" | xargs)
        mem_used=$(echo "$mem_used" | xargs)
        mem_total=$(echo "$mem_total" | xargs)
        power=$(echo "$power" | xargs)
        fan=$(echo "$fan" | xargs)
        clock_gpu=$(echo "$clock_gpu" | xargs)
        clock_mem=$(echo "$clock_mem" | xargs)
        
        echo "┌─────────────────────────────────────────────┐"
        echo "│ GPU $i: $name"
        echo "├─────────────────────────────────────────────┤"
        printf "│ Temperature:   $(color_temp $temp)\n"
        printf "│ GPU Usage:     $(color_util $gpu_util)\n"
        printf "│ Memory Usage:  $(color_util $mem_util)\n"
        echo "│ Memory:        ${mem_used} MB / ${mem_total} MB"
        echo "│ Power:         ${power} W"
        echo "│ Fan Speed:     ${fan}%"
        echo "│ GPU Clock:     ${clock_gpu} MHz"
        echo "│ Memory Clock:  ${clock_mem} MHz"
        echo "└─────────────────────────────────────────────┘"
        echo ""
        
        # Check for alerts
        if [ $temp -ge $CRITICAL_TEMP ]; then
            echo -e "\033[1;31m⚠️  CRITICAL: GPU $i temperature is ${temp}°C!\033[0m"
            echo ""
        elif [ $temp -ge $ALERT_TEMP ]; then
            echo -e "\033[1;33m⚠️  WARNING: GPU $i temperature is ${temp}°C\033[0m"
            echo ""
        fi
    done
    
    # Display system load
    echo "================================================"
    echo "💻 System Load"
    echo "================================================"
    echo ""
    uptime
    echo ""
    free -h | grep Mem | awk '{printf "Memory: %s / %s (%.1f%%)\n", $3, $2, ($3/$2)*100}'
    echo ""
    
    echo "Refreshing in ${REFRESH_INTERVAL}s... (Ctrl+C to stop)"
    
    sleep $REFRESH_INTERVAL
done
