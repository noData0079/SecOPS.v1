#!/bin/bash
set -e

echo "[T79AI Installer] Starting installation..."

SERVER_URL="https://api.t79.ai"
INSTALL_DIR="/opt/t79ai"
PYTHON_BIN="$(command -v python3 || command -v python)"

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

curl -fsSL "$SERVER_URL/agent/latest" > agent.py
curl -fsSL "$SERVER_URL/agent/config" > agent.conf

"$PYTHON_BIN" -m pip install --upgrade t79agent 2>/dev/null || \
  pip install t79agent

echo "[T79AI Installer] Registration…"

NODE_ID=$("$PYTHON_BIN" agent.py register)

echo "NODE_ID=$NODE_ID" >> agent.conf

echo "[T79AI Installer] Creating systemd service..."
cat <<SERVICE >/etc/systemd/system/t79ai.service
[Unit]
Description=T79AI Agent
After=network.target

[Service]
ExecStart=$PYTHON_BIN $INSTALL_DIR/agent.py run
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable t79ai
systemctl start t79ai

echo "Installation complete. This server is now protected by T79AI."
