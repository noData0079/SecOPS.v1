#!/bin/bash
# force-run.sh - Autonomous Brute Force Builder
# Description: Always downloads, builds, and runs. Never exists with failure.
# Ideal for unstable networks or "Ice Age" self-healing.

LOGFILE="$HOME/ice-age-force-run.log"

log() {
    echo "$(date): $1" | tee -a "$LOGFILE"
}

# 1. Fault-Tolerant Retry Logic
retry() {
    local n=0
    local max=5
    local delay=3
    until "$@"; do
        n=$((n+1))
        if [ $n -lt $max ]; then
            log "Command '$1' failed. Attempt $n/$max. Retrying in $delay seconds..."
            sleep $delay
        else
            log "Command '$1' failed after $n attempts. Continuing anyway (Force Mode)..."
            return 0  # CRITICAL: Return success to prevent script exit
        fi
    done
    return 0
}

log "Starting Force Run Sequence"

# 2. OS Dependencies (Debian/Ubuntu)
log "Ensuring OS dependencies..."
retry sudo apt-get update
retry sudo apt-get install -y build-essential git curl python3-pip nodejs npm docker.io docker-compose

# 3. App Dependencies
if [ -f "package.json" ]; then
    log "Found package.json. Installing Node modules..."
    retry npm install
    retry npm run build
fi

if [ -f "requirements.txt" ]; then
    log "Found requirements.txt. Installing Python libs..."
    retry pip3 install -r requirements.txt
fi

# 4. Docker Build & Run
log "Running Docker actions..."
retry sudo docker-compose pull
retry sudo docker-compose build --no-cache
retry sudo docker-compose up -d

log "Force Run Sequence passed."

# 5. Continuous Watch (Optional Loop)
# sleep 3600 && ./force-run.sh
