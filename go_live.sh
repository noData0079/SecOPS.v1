#!/bin/bash
set -e

# Start the application stack
echo ">>> Starting platform..."
docker-compose up -d

# Start Cloudflare Tunnel
echo ">>> Starting Cloudflare Tunnel for laptop-iceage..."
echo ">>> Forwarding via configured tunnel (defined in ~/.cloudflared/config.yml)"

# We run the named tunnel. It reads ~/.cloudflared/config.yml by default.
cloudflared tunnel run laptop-iceage
