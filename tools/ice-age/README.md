# 🧊 ICE-AGE Deployment Toolset

The ICE-AGE (Isolated Computing Environment - Autonomous Governance Engine) deployment suite turns standard hardware into a hardened, autonomous "Bare Metal" host. It is designed for "Sovereign" self-hosting of TSM99 with strict security, offline capabilities, and deterministic recovery.

## ⚠️ Safety Warnings

*   **System Modification**: These scripts (especially `setup.sh` and `offline-mode.sh`) make significant changes to the system configuration, including firewall rules, installed packages, and service management.
*   **Data Overwrite**: `cold-boot-recovery.sh` is designed to **forcefully overwrite** current data with a snapshot. Use with caution.
*   **Network Blocking**: `offline-mode.sh` will block **ALL** outbound traffic (including LAN access) except loopback. Ensure you have physical access or a console session before running.

## Files

*   `setup.sh`: The main "Build Agent" installer. Supports `OFFLINE_MODE` for air-gapped deployments.
*   `offline-mode.sh`: Hardens the network stack to block all non-loopback traffic.
*   `cpu-only-mode.sh`: Configures the environment to force CPU-only inference (default).
*   `cold-boot-recovery.sh`: Manages immutable snapshots and idempotent system restoration.
*   `forensic-replay.sh`: Offline analysis tool for episodic memory.
*   `launcher.sh`: Wrapper for the build agent.

## Deployment Modes

### 1. Online Setup (Standard)
Installs dependencies from the internet.
```bash
# Configure variables in setup.sh first
./setup.sh
```

### 2. Offline / Air-Gapped Setup
Requires pre-downloaded dependencies and repository in place.
```bash
export OFFLINE_MODE=true
./setup.sh
```

## Hardening Features

### Network Isolation
To completely lock down the system network:
```bash
sudo ./offline-mode.sh
```
*   **Blocks**: All outbound Internet and LAN traffic.
*   **Allows**: Loopback (localhost) only.
*   To restore: Run `/root/restore-network.sh`.

### CPU-Only Default
The system defaults to CPU-only inference for maximum compatibility.
To enforce or re-apply:
```bash
sudo ./cpu-only-mode.sh
```

### Deterministic Recovery
To backup or restore the system state idempotently:
```bash
# Create a snapshot
sudo ./cold-boot-recovery.sh create

# Restore (idempotent - skips if data matches)
sudo ./cold-boot-recovery.sh restore <snapshot_name>
```

### Forensic Analysis
Analyze incident logs without network exposure:
```bash
./forensic-replay.sh list
./forensic-replay.sh analyze <incident_id>
```

## Integrity
*   **Deterministic Builds**: `setup.sh` uses `npm ci` (when lockfiles exist) to ensure reproducible dependency trees.
*   **Hash Verification**: `cold-boot-recovery.sh` verifies snapshot integrity before restoration.
