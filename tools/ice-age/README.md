# 🧊 Full Ice Age Deployment Tool

This toolset turns any Ubuntu/Debian laptop or server into a production-ready "Bare Metal" host.
Ideally used for "Sovereign" self-hosting of TSM99 on your own hardware.

## Files
- `setup.sh`: The autonomous "Build Agent" that installs Nginx, Docker, PM2, Postgres, UFW, Certbot, and DDNS.
- `launcher.sh`: Wrapper to run the setup script and log output.
- `ice-age.service`: Systemd unit to keep the agent running forever.

## Resilience Tools

### `force-run.sh`
A "Brute Force" builder script designed to never fail. usage:
```bash
./force-run.sh
```
It will retry every command 5 times, and if it still fails, it **proceeds anyway**. Useful for flaky networks or recovering from partial states.
It can be managed by PM2:
```bash
pm2 start force-run.sh --name ice-age-build --cron "0 * * * *"
```

## Quick Start (On the Laptop Server)


1. **Copy Files**:
   Copy this folder `tools/ice-age` to your server (e.g., `~/ice-age`).

2. **Configure**:
   Edit `setup.sh` to update:
   - `REPO_URL`: Your git repo.
   - `DOMAIN`: Your domain name.
   - `DDNS_`: Your Dynamic DNS credentials (if using home internet).

3. **Install**:
   ```bash
   chmod +x setup.sh launcher.sh
   ./setup.sh
   ```

4. **Persistence (Optional)**:
   To make it auto-heal on reboot:
   ```bash
   sudo cp ice-age.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now ice-age.service
   ```

## What it does
- **Auto-Detects**: Node.js vs Docker apps and configures ports.
- **Security**: Sets up UFW firewall (deny incoming) + Fail2Ban for SSH.
- **SSL**: Auto-renews Let's Encrypt certs.
- **Network**: Updates Dynamic DNS if your home IP changes.
