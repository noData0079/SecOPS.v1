#!/bin/bash
# tools/ice-age/offline-mode.sh
# Enforce offline-only operation - NO outbound traffic

set -e

# Ensure we are root
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

IPTABLES_BACKUP="/root/iptables-backup-$(date +%Y%m%d).rules"

log() {
    echo -e "\033[1;34m[OFFLINE-MODE] $1\033[0m"
}

warn() {
    echo -e "\033[1;33m[WARNING] $1\033[0m"
}

# Backup current rules
log "Backing up current iptables rules to $IPTABLES_BACKUP"
iptables-save > "$IPTABLES_BACKUP"

# Block ALL outbound traffic except essential
log "Configuring firewall for offline-only mode..."

# Allow loopback
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections (for local services)
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Block ALL other outbound (including LAN)
iptables -A OUTPUT -j DROP

log "Offline mode ACTIVATED"
log "All external API calls are now BLOCKED"

# Verify
log "Current outbound rules:"
iptables -L OUTPUT -n -v

# Create restore script
cat > /root/restore-network.sh << 'EOF'
#!/bin/bash
# Restore normal network access
iptables -F OUTPUT
iptables -A OUTPUT -j ACCEPT
echo "Network access restored"
EOF
chmod +x /root/restore-network.sh

log "To restore network: /root/restore-network.sh"
log "Backup saved to: $IPTABLES_BACKUP"
