#!/bin/bash
# ===============================================
# TSM99 - The Sovereign Mechanica
# Production Setup Script v1.0.1
# ===============================================
#
# This script sets up TSM99 in production mode.
# Supports: Full Sovereign (Offline-First) and Connected modes.
#
# Usage:
#   ./setup.sh                    # Interactive mode
#   ./setup.sh --offline          # Ice Age (air-gapped) mode
#   ./setup.sh --quick            # Skip confirmations
# ===============================================

set -e
set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TSM99_VERSION="1.0.1"
TSM99_HOME="${TSM99_HOME:-/opt/tsm99}"
TSM99_DATA="${TSM99_DATA:-/var/lib/tsm99}"
TSM99_LOGS="${TSM99_LOGS:-/var/log/tsm99}"
TSM99_CERTS="${TSM99_CERTS:-/etc/tsm99/certs}"

# Parse arguments
OFFLINE_MODE=false
QUICK_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --offline|--ice-age)
            OFFLINE_MODE=true
            shift
            ;;
        --quick|-y)
            QUICK_MODE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# ===============================================
# Helper Functions
# ===============================================

log() { echo -e "${BLUE}[TSM99]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

confirm() {
    if [ "$QUICK_MODE" = true ]; then
        return 0
    fi
    read -p "$1 [y/N] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# ===============================================
# Banner
# ===============================================

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                                                                     ║"
echo "║   ████████╗███████╗███╗   ███╗ █████╗  █████╗                       ║"
echo "║      ██╔══╝██╔════╝████╗ ████║██╔══██╗██╔══██╗                      ║"
echo "║      ██║   ███████╗██╔████╔██║╚██████║╚██████║                      ║"
echo "║      ██║   ╚════██║██║╚██╔╝██║ ╚═══██║ ╚═══██║                      ║"
echo "║      ██║   ███████║██║ ╚═╝ ██║ █████╔╝ █████╔╝                      ║"
echo "║      ╚═╝   ╚══════╝╚═╝     ╚═╝ ╚════╝  ╚════╝                       ║"
echo "║                                                                     ║"
echo "║   The Sovereign Mechanica - v${TSM99_VERSION}                               ║"
echo "║   Enterprise AI That Heals, Defends & Refines                       ║"
echo "║                                                                     ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

if [ "$OFFLINE_MODE" = true ]; then
    warn "ICE-AGE MODE ENABLED - No outbound network connections"
fi

# ===============================================
# Pre-flight Checks
# ===============================================

log "Running pre-flight checks..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root (sudo ./setup.sh)"
fi

# Check OS
if [ ! -f /etc/os-release ]; then
    error "Cannot detect OS. This script requires Ubuntu/Debian."
fi

source /etc/os-release
log "Detected OS: $PRETTY_NAME"

# Check memory
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_MEM" -lt 8 ]; then
    warn "System has ${TOTAL_MEM}GB RAM. Recommended: 16GB+"
fi

# Check disk space
DISK_FREE=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
if [ "$DISK_FREE" -lt 50 ]; then
    warn "Low disk space: ${DISK_FREE}GB free. Recommended: 100GB+"
fi

success "Pre-flight checks complete"

# ===============================================
# Step 1: Create Directory Structure
# ===============================================

log "Creating directory structure..."

mkdir -p "$TSM99_HOME"
mkdir -p "$TSM99_DATA"/{vault,ledger,models,snapshots,imports}
mkdir -p "$TSM99_LOGS"
mkdir -p "$TSM99_CERTS"
mkdir -p "$TSM99_DATA/memory"/{episodic,semantic,policy,economic}

success "Directories created"

# ===============================================
# Step 2: Install Dependencies
# ===============================================

if [ "$OFFLINE_MODE" != true ]; then
    log "Installing system dependencies..."
    
    apt-get update -qq
    apt-get install -y -qq \
        build-essential \
        curl \
        git \
        python3 \
        python3-pip \
        python3-venv \
        nginx \
        postgresql \
        redis-server \
        docker.io \
        docker-compose \
        ufw \
        fail2ban \
        jq \
        openssl
    
    success "System dependencies installed"
else
    log "Offline mode: Skipping package installation"
fi

# ===============================================
# Step 3: Generate Cryptographic Keys
# ===============================================

log "Generating cryptographic keys..."

if [ ! -f "$TSM99_CERTS/brain_private.pem" ]; then
    openssl genpkey -algorithm ED25519 -out "$TSM99_CERTS/brain_private.pem"
    openssl pkey -in "$TSM99_CERTS/brain_private.pem" -pubout -out "$TSM99_CERTS/brain_public.pem"
    success "Brain keypair generated"
else
    log "Brain keypair already exists"
fi

if [ ! -f "$TSM99_CERTS/vault.key" ]; then
    openssl genrsa -out "$TSM99_CERTS/vault.key" 4096
    openssl req -new -x509 -days 3650 -key "$TSM99_CERTS/vault.key" \
        -out "$TSM99_CERTS/vault.crt" \
        -subj "/C=US/ST=Sovereign/L=Mechanica/O=TSM99/CN=vault.local"
    success "Vault certificate generated"
else
    log "Vault certificate already exists"
fi

# Set permissions
chmod 600 "$TSM99_CERTS"/*.pem "$TSM99_CERTS"/*.key 2>/dev/null || true
chmod 644 "$TSM99_CERTS"/*.crt 2>/dev/null || true

success "Cryptographic keys ready"

# ===============================================
# Step 4: Setup Python Environment
# ===============================================

log "Setting up Python environment..."

VENV_PATH="$TSM99_HOME/venv"
python3 -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"

if [ "$OFFLINE_MODE" != true ]; then
    pip install --upgrade pip -q
    pip install -r backend/requirements.txt -q
    success "Python dependencies installed"
else
    log "Offline mode: Ensure wheels are pre-cached in venv"
fi

# ===============================================
# Step 5: Setup Database
# ===============================================

log "Configuring PostgreSQL..."

sudo -u postgres psql -c "CREATE USER tsm99 WITH PASSWORD 'tsm99_production';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE tsm99_production OWNER tsm99;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tsm99_production TO tsm99;" 2>/dev/null || true

success "Database configured"

# ===============================================
# Step 6: Setup Redis
# ===============================================

log "Configuring Redis..."

systemctl enable redis-server
systemctl start redis-server

success "Redis configured"

# ===============================================
# Step 7: Install Local LLM (Ollama)
# ===============================================

if [ "$OFFLINE_MODE" != true ]; then
    log "Installing Ollama for local LLM..."
    
    if ! command -v ollama &> /dev/null; then
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    
    # Pull Tier 1 and Tier 2 models
    log "Pulling Tier 1 model (phi3:mini)..."
    ollama pull phi3:mini
    
    log "Pulling Tier 2 model (deepseek-coder:6.7b)..."
    ollama pull deepseek-coder:6.7b
    
    success "Local LLM models installed"
else
    log "Offline mode: Ensure models are pre-loaded in /var/lib/tsm99/models"
fi

# ===============================================
# Step 8: Configure Firewall
# ===============================================

log "Configuring firewall..."

ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # API (internal only in production)
ufw allow 3000/tcp  # Frontend (internal only in production)

if [ "$OFFLINE_MODE" = true ]; then
    log "Ice Age: Blocking ALL outbound traffic..."
    ufw default deny outgoing
    ufw allow out on lo  # Allow loopback
fi

ufw --force enable

success "Firewall configured"

# ===============================================
# Step 9: Create Environment File
# ===============================================

log "Creating environment configuration..."

if [ ! -f "$TSM99_HOME/.env" ]; then
    cat > "$TSM99_HOME/.env" << EOF
# TSM99 Production Environment
# Generated: $(date -Iseconds)

ENV=production
API_PORT=8000
API_HOST=0.0.0.0

DATABASE_URL=postgresql://tsm99:tsm99_production@localhost:5432/tsm99_production
REDIS_URL=redis://localhost:6379/0

JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

OLLAMA_HOST=http://localhost:11434
BRAIN_PUBLIC_KEY_PATH=$TSM99_CERTS/brain_public.pem
BRAIN_PRIVATE_KEY_PATH=$TSM99_CERTS/brain_private.pem

ICE_AGE_ENABLED=$OFFLINE_MODE
OFFLINE_MODE=$OFFLINE_MODE

DAILY_BUDGET_USD=100.00
EMERGENCY_CUTOFF_ENABLED=true
EOF
    success "Environment file created"
else
    log "Environment file already exists"
fi

# ===============================================
# Step 10: Create Systemd Services
# ===============================================

log "Creating systemd services..."

# Backend service
cat > /etc/systemd/system/tsm99-backend.service << EOF
[Unit]
Description=TSM99 Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=$TSM99_HOME/backend
Environment="PATH=$VENV_PATH/bin"
EnvironmentFile=$TSM99_HOME/.env
ExecStart=$VENV_PATH/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Frontend service
cat > /etc/systemd/system/tsm99-frontend.service << EOF
[Unit]
Description=TSM99 Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$TSM99_HOME/frontend
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable tsm99-backend tsm99-frontend

success "Systemd services created"

# ===============================================
# Step 11: Initialize Trust Ledger
# ===============================================

log "Initializing Trust Ledger..."

LEDGER_PATH="$TSM99_DATA/vault/ledger.db"
if [ ! -f "$LEDGER_PATH" ]; then
    sqlite3 "$LEDGER_PATH" << EOF
CREATE TABLE IF NOT EXISTS event_log (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    payload TEXT NOT NULL,
    hash TEXT NOT NULL,
    prev_hash TEXT
);

CREATE TABLE IF NOT EXISTS decision_trace (
    decision_id TEXT PRIMARY KEY,
    event_id TEXT,
    model_version TEXT,
    policy_version TEXT,
    prompt_hash TEXT,
    input_features TEXT,
    output_action TEXT,
    confidence REAL,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS learning_delta (
    delta_id TEXT PRIMARY KEY,
    decision_id TEXT,
    affected_component TEXT,
    before_hash TEXT,
    after_hash TEXT,
    delta_blob BLOB,
    reason TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    snapshot_type TEXT,
    created_at TEXT,
    state_hash TEXT,
    metadata TEXT
);
EOF
    success "Trust Ledger initialized"
else
    log "Trust Ledger already exists"
fi

# ===============================================
# Step 12: Create Golden Baseline
# ===============================================

log "Creating Golden Baseline snapshot..."

BASELINE_PATH="$TSM99_DATA/memory/golden_baseline.json"
cat > "$BASELINE_PATH" << EOF
{
    "version": "$TSM99_VERSION",
    "created_at": "$(date -Iseconds)",
    "confidence_baseline": 0.60,
    "policy_version": "1.0.0",
    "axioms": {
        "never_allow_production_delete_without_approval": true,
        "require_mfa_for_admin_actions": true,
        "block_known_malware_hashes": true,
        "rate_limit_api_calls": true
    },
    "learning_enabled": true,
    "shadow_mode": true
}
EOF

success "Golden Baseline created"

# ===============================================
# Final Status
# ===============================================

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                 TSM99 INSTALLATION COMPLETE                         ║"
echo "╠════════════════════════════════════════════════════════════════════╣"
echo "║                                                                     ║"
echo "║  Version:        $TSM99_VERSION                                           ║"
echo "║  Mode:           $([ "$OFFLINE_MODE" = true ] && echo "ICE-AGE (Air-Gapped)" || echo "CONNECTED")                       ║"
echo "║                                                                     ║"
echo "║  Directories:                                                       ║"
echo "║    Home:         $TSM99_HOME                                        ║"
echo "║    Data:         $TSM99_DATA                                        ║"
echo "║    Logs:         $TSM99_LOGS                                        ║"
echo "║                                                                     ║"
echo "║  Services:                                                          ║"
echo "║    Backend:      sudo systemctl start tsm99-backend                 ║"
echo "║    Frontend:     sudo systemctl start tsm99-frontend                ║"
echo "║                                                                     ║"
echo "║  Access:                                                            ║"
echo "║    Dashboard:    http://localhost:3000                              ║"
echo "║    API Docs:     http://localhost:8000/docs                         ║"
echo "║                                                                     ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

success "TSM99 - The Sovereign Mechanica is ready!"
echo ""
log "Next steps:"
echo "  1. Review configuration: $TSM99_HOME/.env"
echo "  2. Start services: sudo systemctl start tsm99-backend tsm99-frontend"
echo "  3. Access dashboard: http://localhost:3000"
echo ""
