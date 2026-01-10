#!/bin/bash
# tools/setup-wsl-ml.sh
# Automates the "Manual Work" done by the user to set up a robust ML stack on WSL/Ubuntu.
# Installs Python 3.10/3.11, Build Essentials, and ML dependencies (Torch, vLLM).

set -e

log() {
    echo -e "\033[1;32m[SETUP] $1\033[0m"
}

log "Updating Apt Repositories..."
sudo apt update && sudo apt upgrade -y

log "Installing Core Build Tools..."
sudo apt install -y build-essential git curl software-properties-common

log "Adding Deadsnakes PPA (for Python 3.10/3.11)..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

log "Installing Python 3.10 & 3.11 with Venv/Dev headers..."
# vLLM often prefers 3.10 or 3.11 over the system default if it's too new or old
sudo apt install -y \
    python3.10 python3.10-venv python3.10-dev \
    python3.11 python3.11-venv python3.11-dev

log "Creating Virtual Environment (python3.11)..."
# Create venv if not exists
if [ ! -d ".venv" ]; then
    python3.11 -m venv .venv
    log "Virtual Environment created at .venv"
else
    log "Virtual Environment already exists."
fi

log "Installing Dependencies (including vLLM/Torch for Linux)..."
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
if [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
    log "Backend dependencies installed."
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    log "Dependencies installed."
else
    log "Warning: requirements.txt not found. Skipping pip install."
fi

log "Installation Complete."
echo "To activate: source .venv/bin/activate"

