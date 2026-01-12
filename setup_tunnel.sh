#!/bin/bash
set -e

# 1. System Check & Install
echo ">>> detecting OS..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo ">>> Linux detected."
    if ! command -v cloudflared &> /dev/null; then
        echo ">>> Installing cloudflared..."
        # Using the official .deb for stability (assuming Debian-based as is common)
        if [ -f /etc/debian_version ]; then
             curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
             sudo dpkg -i cloudflared.deb || { echo "dpkg failed, trying apt-get fix"; sudo apt-get install -f; }
             rm cloudflared.deb
        else
             # Generic linux binary install
             echo ">>> Non-Debian Linux detected. Downloading binary..."
             curl -L --output cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
             chmod +x cloudflared
             sudo mv cloudflared /usr/local/bin/
        fi
    else
        echo ">>> cloudflared already installed."
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo ">>> Windows detected. Please run: winget install --id Cloudflare.cloudflared"
    exit 1
else
    echo ">>> OS not fully supported by this auto-script. Please install cloudflared manually."
    exit 1
fi

# 2. Login
echo ">>> Please log in to Cloudflare (opens browser)..."
cloudflared tunnel login

# 3. Create Tunnel
echo ">>> Creating tunnel 'laptop-iceage'..."
# Create tunnel and capture output to find UUID if needed, but 'create' saves creds to default location.
# We use || true to prevent failure if it exists.
cloudflared tunnel create laptop-iceage || echo "Tunnel might already exist, proceeding..."

# 4. Generate Configuration
# We need the Tunnel UUID.
# Assuming standard path: ~/.cloudflared/<UUID>.json
echo ">>> Configuring tunnel..."
TUNNEL_ID=$(cloudflared tunnel list | grep laptop-iceage | awk '{print $1}')

if [ -z "$TUNNEL_ID" ]; then
    echo "Error: Could not find tunnel ID for laptop-iceage. Did creation fail?"
    exit 1
fi

echo ">>> Detected Tunnel ID: $TUNNEL_ID"
CRED_FILE="$HOME/.cloudflared/$TUNNEL_ID.json"

# Ask for Port
echo ""
echo ">>> Enter the local port your app is running on (default: 3000):"
read -r APP_PORT
APP_PORT=${APP_PORT:-3000}

# Ask for Domain
echo ""
echo ">>> Enter your desired domain name (e.g., app.mydomain.com):"
read -r DOMAIN_NAME

mkdir -p ~/.cloudflared

if [ -n "$DOMAIN_NAME" ]; then
    echo ">>> Routing $DOMAIN_NAME to this tunnel..."
    cloudflared tunnel route dns laptop-iceage "$DOMAIN_NAME"

    # Create config.yml with hostname
    cat <<EOF > ~/.cloudflared/config.yml
tunnel: $TUNNEL_ID
credentials-file: $CRED_FILE

ingress:
  - hostname: $DOMAIN_NAME
    service: http://localhost:$APP_PORT
  - service: http_status:404
EOF
    echo ">>> Config generated at ~/.cloudflared/config.yml (Port: $APP_PORT, Domain: $DOMAIN_NAME)"
else
    echo ">>> No domain provided. Skipping DNS routing."
    # Basic config without hostname restriction
    cat <<EOF > ~/.cloudflared/config.yml
tunnel: $TUNNEL_ID
credentials-file: $CRED_FILE

ingress:
  - service: http://localhost:$APP_PORT
EOF
    echo ">>> Config generated at ~/.cloudflared/config.yml (Port: $APP_PORT)"
fi

echo ">>> Setup complete! Run ./go_live.sh to start."
