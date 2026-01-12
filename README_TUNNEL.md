# Cloudflare Tunnel Setup & Instructions

This guide helps you set up a permanent, globally accessible URL for your laptop-hosted platform, bypassing dynamic IP issues.

## 1. Prerequisites (OS Detection)

The provided scripts are optimized for **Linux**.

### Windows Users
If you are on Windows, you must install `cloudflared` manually via PowerShell:
```powershell
winget install --id Cloudflare.cloudflared
```
Then run the commands in `setup_tunnel.sh` manually in your terminal, or use WSL (Windows Subsystem for Linux).

### Linux Users
The `setup_tunnel.sh` script handles installation for Debian/Ubuntu and generic Linux distributions using `curl` and `dpkg`.

---

## 2. Setup (One-Time)

Run the setup script to install Cloudflare, authenticate, create the tunnel, and route your domain.

```bash
chmod +x setup_tunnel.sh
./setup_tunnel.sh
```

**What it does:**
1.  Installs `cloudflared`.
2.  Opens a browser for you to log in to Cloudflare.
3.  Creates a tunnel named `laptop-iceage`.
4.  Asks for your domain (e.g., `app.mydomain.com`) and creates a DNS CNAME record pointing to your tunnel.

---

## 3. Go Live (Daily Usage)

To start your platform and the tunnel:

```bash
chmod +x go_live.sh
./go_live.sh
```

This will:
1.  Start your app stack (`docker-compose up -d`).
2.  Start the tunnel, forwarding `http://localhost:3000` (Frontend) to the internet.

**Note:** Keep this terminal window open to keep the tunnel running.

---

## 4. Fallback Plan: Tailscale Funnel

If Cloudflare Tunnel fails or is blocked, use **Tailscale Funnel** as a backup.

1.  **Install Tailscale:** [https://tailscale.com/download](https://tailscale.com/download)
2.  **Enable Funnel:**
    ```bash
    tailscale serve --bg 3000
    tailscale funnel 3000 on
    ```
3.  **Access:** Tailscale will provide a URL (e.g., `https://machine-name.tailscale.ts.net`) that is publicly accessible.

---

## Troubleshooting

-   **Tunnel already exists:** The setup script handles this warning gracefully.
-   **Port 3000 not reachable:** Ensure your frontend container is running (`docker ps`).
-   **Backend Access:** Currently, only port 3000 is exposed. If your frontend tries to reach the backend at `localhost:8000`, it will fail for external users. You may need to configure Next.js rewrites or expose the backend via a separate tunnel/ingress rule.
