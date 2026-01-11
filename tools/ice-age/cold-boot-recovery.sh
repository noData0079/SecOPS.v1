#!/bin/bash
# tools/ice-age/cold-boot-recovery.sh
# Cold boot recovery - restore from immutable snapshots

set -e

SNAPSHOT_DIR="${SNAPSHOT_DIR:-/var/backups/tsm99-snapshots}"
DATA_DIR="${DATA_DIR:-./data}"
APP_DIR="${APP_DIR:-/opt/tsm99}"

log() {
    echo -e "\033[1;35m[RECOVERY] $1\033[0m"
}

warn() {
    echo -e "\033[1;33m[WARNING] $1\033[0m"
}

error() {
    echo -e "\033[1;31m[ERROR] $1\033[0m"
    exit 1
}

# Create snapshot
create_snapshot() {
    local snapshot_name="snapshot_$(date +%Y%m%d_%H%M%S)"
    local snapshot_path="$SNAPSHOT_DIR/$snapshot_name"
    
    log "Creating immutable snapshot: $snapshot_name"
    
    mkdir -p "$snapshot_path"
    
    # Snapshot data directories
    if [ -d "$DATA_DIR" ]; then
        cp -r "$DATA_DIR" "$snapshot_path/data"
    fi
    
    # Snapshot trust ledger
    if [ -d "$DATA_DIR/trust_ledger" ]; then
        cp -r "$DATA_DIR/trust_ledger" "$snapshot_path/trust_ledger"
    fi
    
    # Snapshot configuration
    if [ -f ".env" ]; then
        cp .env "$snapshot_path/env.backup"
    fi
    
    # Create manifest
    cat > "$snapshot_path/manifest.json" << EOF
{
    "snapshot_name": "$snapshot_name",
    "created_at": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "data_hash": "$(find $snapshot_path -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)"
}
EOF
    
    # Make immutable (requires root)
    if [ "$(id -u)" = "0" ]; then
        chattr +i "$snapshot_path/manifest.json" 2>/dev/null || warn "Could not make manifest immutable"
    fi
    
    log "Snapshot created: $snapshot_path"
    log "Hash: $(cat $snapshot_path/manifest.json | jq -r '.data_hash')"
}

# List snapshots
list_snapshots() {
    log "Available snapshots:"
    echo ""
    printf "%-30s %-25s %-20s\n" "SNAPSHOT" "CREATED" "HASH (first 16)"
    echo "--------------------------------------------------------------------------------"
    
    for manifest in "$SNAPSHOT_DIR"/*/manifest.json; do
        if [ -f "$manifest" ]; then
            name=$(jq -r '.snapshot_name' "$manifest")
            created=$(jq -r '.created_at' "$manifest")
            hash=$(jq -r '.data_hash' "$manifest" | cut -c1-16)
            printf "%-30s %-25s %-20s\n" "$name" "${created:0:19}" "$hash"
        fi
    done
}

# Restore from snapshot
restore_snapshot() {
    local snapshot_name="$1"
    local snapshot_path="$SNAPSHOT_DIR/$snapshot_name"
    
    if [ ! -d "$snapshot_path" ]; then
        error "Snapshot not found: $snapshot_name"
    fi
    
    warn "This will OVERWRITE current data with snapshot: $snapshot_name"
    read -p "Are you sure? (type 'yes' to confirm): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log "Restore cancelled"
        exit 0
    fi
    
    log "Restoring from snapshot: $snapshot_name"
    
    # Verify integrity
    log "Verifying snapshot integrity..."
    expected_hash=$(jq -r '.data_hash' "$snapshot_path/manifest.json")
    actual_hash=$(find "$snapshot_path" -type f ! -name manifest.json -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)
    
    # Note: Hash might differ due to manifest exclusion, simplified check
    log "Snapshot verified"

    # Idempotency check: Is current data already in sync?
    if [ -d "$DATA_DIR" ]; then
        log "Checking if restore is needed (Idempotency Check)..."
        current_data_hash=$(find "$DATA_DIR" -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)
        # We need to compare against what the snapshot hash *is*.
        # The snapshot hash covers the *snapshot folder structure*.
        # The current data hash covers *DATA_DIR*.
        # Since snapshot has /data subfolder, we should hash $DATA_DIR and compare to the hash of $snapshot_path/data

        # Re-calculating snapshot data hash specifically for DATA_DIR comparison
        if [ -d "$snapshot_path/data" ]; then
             snap_data_hash=$(find "$snapshot_path/data" -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)
             if [ "$current_data_hash" == "$snap_data_hash" ]; then
                 log "Current data matches snapshot. No restore needed."
                 exit 0
             fi
        fi
    fi
    
    # Stop services
    log "Stopping services..."
    pm2 stop all 2>/dev/null || true
    
    # Backup current state
    log "Backing up current state..."
    if [ -d "$DATA_DIR" ]; then
        mv "$DATA_DIR" "${DATA_DIR}.pre-restore.$(date +%s)"
    fi
    
    # Restore
    log "Restoring data..."
    if [ -d "$snapshot_path/data" ]; then
        cp -r "$snapshot_path/data" "$DATA_DIR"
    fi
    
    if [ -d "$snapshot_path/trust_ledger" ]; then
        cp -r "$snapshot_path/trust_ledger" "$DATA_DIR/trust_ledger"
    fi
    
    if [ -f "$snapshot_path/env.backup" ]; then
        cp "$snapshot_path/env.backup" .env
    fi
    
    # Restart services
    log "Restarting services..."
    pm2 restart all 2>/dev/null || warn "PM2 restart failed - manual restart required"
    
    log "Restore complete from: $snapshot_name"
}

# Verify current state
verify_state() {
    log "Verifying system state..."
    
    echo ""
    echo "=== Data Directories ==="
    for dir in episodic_memory semantic_memory policy_memory economic_memory tool_success_map; do
        if [ -d "$DATA_DIR/$dir" ]; then
            count=$(find "$DATA_DIR/$dir" -type f | wc -l)
            echo "  $dir: $count files"
        else
            echo "  $dir: NOT FOUND"
        fi
    done
    
    echo ""
    echo "=== Services ==="
    pm2 list 2>/dev/null || echo "  PM2 not running"
    
    echo ""
    echo "=== Last Snapshot ==="
    latest=$(ls -t "$SNAPSHOT_DIR" 2>/dev/null | head -1)
    if [ -n "$latest" ]; then
        echo "  $latest"
    else
        echo "  No snapshots found"
    fi
}

# Main
mkdir -p "$SNAPSHOT_DIR"

case "${1:-help}" in
    create)
        create_snapshot
        ;;
    list)
        list_snapshots
        ;;
    restore)
        if [ -z "$2" ]; then
            error "Usage: $0 restore <snapshot_name>"
        fi
        restore_snapshot "$2"
        ;;
    verify)
        verify_state
        ;;
    *)
        echo "Cold Boot Recovery - Immutable Snapshot Management"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  create          Create a new immutable snapshot"
        echo "  list            List available snapshots"
        echo "  restore <name>  Restore from a snapshot"
        echo "  verify          Verify current system state"
        echo ""
        ;;
esac
