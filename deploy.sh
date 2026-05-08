#!/bin/bash
# Full deploy: kills old servers, installs fresh service on port 5000

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Run as root: sudo ./deploy.sh"
    exit 1
fi

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE="nvidia-gpu-benchmark"
INSTALL_DIR="/opt/nvidia-gpu-benchmark"

echo "=== Stopping all old servers ==="
systemctl stop "$SERVICE" 2>/dev/null || true
pkill -9 -f "python3.*server.py" 2>/dev/null || true
pkill -9 -f "server.py" 2>/dev/null || true
sleep 2
# Force free ports 5000 and 5001
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 5001/tcp 2>/dev/null || true
sleep 2
echo "Done"

echo "=== Removing old installation ==="
systemctl disable "$SERVICE" 2>/dev/null || true
rm -f /etc/systemd/system/${SERVICE}.service
rm -rf "$INSTALL_DIR"
systemctl daemon-reload
echo "Done"

echo "=== Creating fresh installation at $INSTALL_DIR ==="
mkdir -p "$INSTALL_DIR"
cp -r "$SRC"/* "$INSTALL_DIR/"

# Create venv if not exists
if [ ! -f "$INSTALL_DIR/venv/bin/python3" ]; then
    echo "Creating venv..."
    python3 -m venv "$INSTALL_DIR/venv"
fi

echo "Installing dependencies..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

echo "Installing CuPy..."
"$INSTALL_DIR/venv/bin/pip" install cupy-cuda12x -q 2>/dev/null && echo "CuPy installed" || \
"$INSTALL_DIR/venv/bin/pip" install cupy-cuda11x -q 2>/dev/null && echo "CuPy installed (11x)" || \
echo "CuPy not installed (optional)"

mkdir -p "$INSTALL_DIR/logs"
chown -R noname:noname "$INSTALL_DIR"
echo "Done"

echo "=== Verifying port 5000 in config ==="
python3 -c "
import json
with open('$INSTALL_DIR/config.json') as f:
    c = json.load(f)
c['server']['port'] = 5000
with open('$INSTALL_DIR/config.json', 'w') as f:
    json.dump(c, f, indent=2)
print('Port set to:', c['server']['port'])
"

echo "=== Creating systemd service ==="
cat > "/etc/systemd/system/${SERVICE}.service" << EOF
[Unit]
Description=NVIDIA GPU Benchmark Tool
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="HOME=/root"
ExecStart=${INSTALL_DIR}/venv/bin/python3 ${INSTALL_DIR}/server.py
Restart=on-failure
RestartSec=10
StandardOutput=append:${INSTALL_DIR}/logs/service.log
StandardError=append:${INSTALL_DIR}/logs/service_error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl start "$SERVICE"
sleep 3

if systemctl is-active --quiet "$SERVICE"; then
    echo ""
    echo "=========================================="
    echo "  Service running on http://localhost:5000"
    echo "=========================================="
    curl -s http://localhost:5000/api/status
    echo ""
else
    echo "FAILED - check logs:"
    journalctl -u "$SERVICE" -n 20 --no-pager
    exit 1
fi
