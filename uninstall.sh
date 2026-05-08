#!/bin/bash

# Uninstall Script for NVIDIA GPU Benchmark Tool

set -e

SERVICE_NAME="nvidia-gpu-benchmark"
INSTALL_DIR="/opt/nvidia-gpu-benchmark"

echo "================================================"
echo "NVIDIA GPU Benchmark Tool - Uninstall"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Stop service if running
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo "⏹️  Stopping service..."
    systemctl stop "$SERVICE_NAME"
    echo "✓ Service stopped"
fi

# Disable service
if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo "🔓 Disabling service..."
    systemctl disable "$SERVICE_NAME"
    echo "✓ Service disabled"
fi

# Remove service file
if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    echo "🗑️  Removing service file..."
    rm "/etc/systemd/system/${SERVICE_NAME}.service"
    systemctl daemon-reload
    echo "✓ Service file removed"
fi

# Ask before removing installation directory
if [ -d "$INSTALL_DIR" ]; then
    echo ""
    read -p "Remove installation directory $INSTALL_DIR? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing installation directory..."
        rm -rf "$INSTALL_DIR"
        echo "✓ Installation directory removed"
    else
        echo "⏭️  Keeping installation directory"
    fi
fi

echo ""
echo "================================================"
echo "✅ Uninstall completed"
echo "================================================"
echo ""
echo "To reinstall, run: sudo ./install.sh"
echo ""
