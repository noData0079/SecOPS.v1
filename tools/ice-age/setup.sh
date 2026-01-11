#!/bin/bash
# ===============================================
# Full Ice Age Autonomous Server & Build Agent
# Fully plug-and-play: auto-detects app port, Nginx, SSL, PM2, Docker, PostgreSQL, DDNS
# Never stops, auto-downloads dependencies, rebuilds containers
# ===============================================

set -e
set -o pipefail

# Safety Warnings
echo "================================================================"
echo "WARNING: This script performs extensive system modifications."
echo "It installs packages, changes firewall rules, and manages services."
echo "Ensure you have inspected the code before running."
echo "================================================================"

# Check for Offline Mode
if [ -z "$OFFLINE_MODE" ]; then
    OFFLINE_MODE="false"
fi

if [ "$OFFLINE_MODE" == "true" ]; then
    echo "[SETUP] OFFLINE MODE ACTIVE. Skipping network operations."
fi

# ---------------------------
# Retry helper
# ---------------------------
retry() {
    if [ "$OFFLINE_MODE" == "true" ]; then
        # In offline mode, if it's a network command, we might want to skip or fail?
        # But this helper is generic. We will wrap network calls instead.
        "$@"
        return $?
    fi
    local n=0
    local max=5
    local delay=3
    until "$@"; do
        exit=$?
        n=$((n+1))
        if [ $n -lt $max ]; then
            echo "Command failed. Attempt $n/$max. Retrying in $delay seconds..."
            sleep $delay
        else
            echo "Command failed after $n attempts. Continuing anyway..."
            return $exit
        fi
    done
    return 0
}

log() { echo -e "\n========== $1 =========="; }

# ---------------------------
# 1. System Update & Essentials
# ---------------------------
log "Updating system & installing essentials"
if [ "$OFFLINE_MODE" != "true" ]; then
    retry sudo apt update
    retry sudo apt -y upgrade
    retry sudo apt install -y build-essential curl git ufw fail2ban software-properties-common docker.io docker-compose python3-pip lsof
else
    log "Offline mode: Skipping apt update/install. Assuming packages are present."
fi

retry sudo systemctl enable --now docker

# ---------------------------
# 2. Node.js & PM2
# ---------------------------
log "Installing Node.js & PM2"
if [ "$OFFLINE_MODE" != "true" ]; then
    echo "WARNING: Downloading and executing remote script from nodesource.com"
    retry curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    retry sudo apt install -y nodejs
    retry sudo npm install -g pm2
else
    log "Offline mode: Skipping Node.js download/install."
fi

# ---------------------------
# 3. Nginx
# ---------------------------
log "Installing Nginx"
if [ "$OFFLINE_MODE" != "true" ]; then
    retry sudo apt install -y nginx
fi
retry sudo systemctl enable --now nginx

# ---------------------------
# 4. Firewall & Security
# ---------------------------
log "Configuring UFW & Fail2Ban"
retry sudo ufw allow ssh
retry sudo ufw allow 'Nginx Full'
retry sudo ufw default deny incoming
retry sudo ufw default allow outgoing
retry sudo ufw --force enable
retry sudo systemctl enable --now fail2ban

# ---------------------------
# 5. App Repo & Dependencies
# ---------------------------
APP_DIR="$HOME/full-ice-age-app"
REPO_URL="https://github.com/username/your-app.git"  # Replace with your repo
APP_START_CMD="index.js" # Replace with your entry file

log "Cloning/updating app repository"
if [ ! -d "$APP_DIR" ]; then
    if [ "$OFFLINE_MODE" != "true" ]; then
        retry git clone "$REPO_URL" "$APP_DIR"
    else
        echo "ERROR: App directory $APP_DIR does not exist and OFFLINE_MODE is on."
        exit 1
    fi
else
    cd "$APP_DIR"
    if [ "$OFFLINE_MODE" != "true" ]; then
        retry git pull
    fi
fi
cd "$APP_DIR"

if [ -f "package.json" ]; then
    log "Installing Node.js dependencies"
    # Deterministic build
    if [ -f "package-lock.json" ]; then
        retry npm ci
    else
        retry npm install
    fi
fi
if [ -f "requirements.txt" ]; then
    log "Installing Python dependencies"
    retry pip3 install -r requirements.txt
fi

# ---------------------------
# 6. Docker Auto-Build & Run
# ---------------------------
if [ -f "Dockerfile" ]; then
    log "Building Docker container"
    retry sudo docker build -t full-ice-age-app .
fi
if [ -f "docker-compose.yml" ]; then
    log "Running Docker Compose"
    retry sudo docker-compose up -d --build
fi

# ---------------------------
# 7. Auto-Detect App Port
# ---------------------------
log "Detecting running app port..."
APP_PORT=3000 # Default fallback
# Node/PM2 process detection
if pm2 list | grep -q "$APP_START_CMD"; then
    APP_PORT=$(pm2 info "$APP_START_CMD" | grep "port" | grep -oE '[0-9]{2,5}' || echo 3000)
fi
# Docker detection
if docker ps | grep -q "full-ice-age-app"; then
    APP_PORT=$(docker ps --format '{{.Ports}}' | grep -oE '[0-9]{2,5}->' | head -1 | grep -oE '[0-9]{2,5}' || echo 3000)
fi
log "Using app port: $APP_PORT"

# ---------------------------
# 8. Nginx Reverse Proxy
# ---------------------------
DOMAIN="yourdomain.com" # Replace with your domain
NGINX_CONF="/etc/nginx/sites-available/full-ice-age"
TEMPLATE_NGINX="./templates/nginx_app.conf"

log "Configuring Nginx reverse proxy for port $APP_PORT"

if [ -f "$TEMPLATE_NGINX" ]; then
    sudo cp "$TEMPLATE_NGINX" "$NGINX_CONF"
    # Replace variables in the config file
    sudo sed -i "s/\${DOMAIN}/$DOMAIN/g" "$NGINX_CONF"
    sudo sed -i "s/\${APP_PORT}/$APP_PORT/g" "$NGINX_CONF"
else
    log "Error: Nginx template not found at $TEMPLATE_NGINX"
    exit 1
fi

retry sudo ln -sf /etc/nginx/sites-available/full-ice-age /etc/nginx/sites-enabled/
retry sudo nginx -t
retry sudo systemctl restart nginx

# ---------------------------
# 9. Certbot SSL
# ---------------------------
log "Installing Certbot & obtaining SSL"
if [ "$OFFLINE_MODE" != "true" ]; then
    retry sudo apt install -y certbot python3-certbot-nginx
    retry sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN
    retry sudo certbot renew --dry-run
else
    log "Offline mode: Skipping Certbot."
fi

# ---------------------------
# 10. PM2 Auto-Start
# ---------------------------
log "Starting app with PM2"
retry pm2 start "$APP_START_CMD" --name "full-ice-age-app"
retry pm2 startup systemd -u $(whoami) --hp $(eval echo ~$USER)
retry pm2 save

# ---------------------------
# 11. PostgreSQL
# ---------------------------
log "Installing PostgreSQL"
retry sudo apt install -y postgresql postgresql-contrib
retry sudo systemctl enable --now postgresql

# ---------------------------
# 12. Automated DDNS / Dynamic IP Updater
# ---------------------------
DDNS_PROVIDER="duckdns"  # or "noip"
DDNS_TOKEN="YOUR_DDNS_TOKEN"
DDNS_DOMAIN="your-subdomain"
UPDATE_INTERVAL=300

log "Setting up automated DDNS updater"

DDNS_SCRIPT="$HOME/ddns_update.sh"
TEMPLATE_DDNS="./templates/ddns_update.sh"

if [ -f "$TEMPLATE_DDNS" ]; then
    cp "$TEMPLATE_DDNS" "$DDNS_SCRIPT"
    
    # Inject variables
    sed -i "s/\${DDNS_PROVIDER}/$DDNS_PROVIDER/g" "$DDNS_SCRIPT"
    sed -i "s/\${DDNS_TOKEN}/$DDNS_TOKEN/g" "$DDNS_SCRIPT"
    sed -i "s/\${DDNS_DOMAIN}/$DDNS_DOMAIN/g" "$DDNS_SCRIPT"
    
    chmod +x "$DDNS_SCRIPT"
    
    # Cron job
    (crontab -l 2>/dev/null; echo "*/5 * * * * $DDNS_SCRIPT") | crontab -
    log "DDNS updater installed. Updates every 5 minutes."
else
    log "Error: DDNS template not found at $TEMPLATE_DDNS"
fi

# ---------------------------
# 13. Final Status
# ---------------------------
log "Final verification:"
sudo ufw status verbose
sudo systemctl status nginx | head -10
pm2 list
sudo certbot certificates
docker ps -a

echo "✅ Full Ice Age Autonomous Server setup complete! Your server is now plug-and-play with auto port detection, Nginx, SSL, PM2, Docker, PostgreSQL, and DDNS updates."
