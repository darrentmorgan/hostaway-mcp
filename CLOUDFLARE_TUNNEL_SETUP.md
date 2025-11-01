# Cloudflare Tunnel Setup Guide
## For mcp.baliluxurystays.com

This guide will set up free HTTPS for your Hostaway MCP server using Cloudflare Tunnel.

---

## Prerequisites

✅ Domain: `baliluxurystays.com`
✅ Cloudflare account (free tier is fine)
✅ SSH access to Hostinger VPS: `72.60.233.157`

---

## Setup Overview

Cloudflare Tunnel will:
- Give you **free HTTPS** (`https://mcp.baliluxurystays.com`)
- Handle SSL/TLS certificates automatically
- Provide DDoS protection
- No need to open ports or configure firewalls

**Time required:** ~10 minutes

---

## Step-by-Step Setup

### Step 0: Ensure Domain is on Cloudflare

**Check if `baliluxurystays.com` is using Cloudflare nameservers:**

1. Go to https://www.cloudflare.com/
2. Log in to your account
3. Check if `baliluxurystays.com` is listed in your domains

**If NOT on Cloudflare yet:**
1. Click "Add a site" in Cloudflare dashboard
2. Enter `baliluxurystays.com`
3. Follow prompts to change nameservers at your domain registrar
4. Wait for DNS propagation (~5-30 minutes)

---

### Step 1: Copy Setup Script to VPS

**On your local machine:**

```bash
# Copy the setup script to your VPS
scp scripts/setup-cloudflare-tunnel-baliluxurystays.sh root@72.60.233.157:/root/
```

---

### Step 2: SSH into Hostinger VPS

```bash
ssh root@72.60.233.157
```

---

### Step 3: Run the Setup Script

**On the VPS:**

```bash
# Make script executable (if not already)
chmod +x /root/setup-cloudflare-tunnel-baliluxurystays.sh

# Run the setup script
bash /root/setup-cloudflare-tunnel-baliluxurystays.sh
```

**What the script does:**
1. ✅ Installs `cloudflared` (if not already installed)
2. ✅ Opens browser for Cloudflare authentication
3. ✅ Creates tunnel named `hostaway-mcp`
4. ✅ Configures tunnel to point `mcp.baliluxurystays.com` → `localhost:8080`
5. ✅ Routes DNS automatically in Cloudflare
6. ✅ Installs tunnel as a system service
7. ✅ Starts the tunnel

---

### Step 4: Verify Setup

**Test the HTTPS endpoint:**

```bash
# From VPS or local machine
curl https://mcp.baliluxurystays.com/health
```

**Expected response:**
```json
{"status": "healthy"}
```

---

### Step 5: Configure Claude MCP Connector

In Claude Desktop, add custom connector:

```
Name: Hostaway MCP
Remote MCP server: https://mcp.baliluxurystays.com
OAuth Client ID: (leave empty)
OAuth Client Secret: (leave empty)
```

✅ Click "Add" and confirm trust

---

## Management Commands

### Check Tunnel Status
```bash
sudo systemctl status cloudflared
```

### View Tunnel Logs
```bash
sudo journalctl -u cloudflared -f
```

### Restart Tunnel
```bash
sudo systemctl restart cloudflared
```

### Stop Tunnel
```bash
sudo systemctl stop cloudflared
```

### List Tunnels
```bash
cloudflared tunnel list
```

---

## Troubleshooting

### Issue: "Tunnel not connecting"

**Check:**
1. Is the MCP server running? `docker ps`
2. Is the tunnel service running? `systemctl status cloudflared`
3. Check tunnel logs: `journalctl -u cloudflared -f`

### Issue: "DNS not resolving"

**Wait 1-2 minutes** for DNS propagation, then:
```bash
nslookup mcp.baliluxurystays.com
```

Should show Cloudflare IP addresses.

### Issue: "Authentication failed"

**Re-authenticate:**
```bash
cloudflared tunnel login
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Client (Claude Desktop)                        │
│  Connects to: https://mcp.baliluxurystays.com   │
└─────────────────┬───────────────────────────────┘
                  │ HTTPS (443)
                  ▼
┌─────────────────────────────────────────────────┐
│  Cloudflare Network                             │
│  - Handles HTTPS/TLS                            │
│  - DDoS protection                              │
│  - Global CDN                                   │
└─────────────────┬───────────────────────────────┘
                  │ Encrypted Tunnel
                  ▼
┌─────────────────────────────────────────────────┐
│  Hostinger VPS (72.60.233.157)                  │
│  ┌─────────────────────────────────────────┐   │
│  │ cloudflared                             │   │
│  │ Listens: cloudflare tunnel              │   │
│  │ Forwards to: localhost:8080             │   │
│  └──────────────┬──────────────────────────┘   │
│                 │ HTTP (internal)               │
│  ┌──────────────▼──────────────────────────┐   │
│  │ Docker: hostaway-mcp                    │   │
│  │ Port: 8080                              │   │
│  │ MCP Server (FastAPI)                    │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## Benefits

✅ **Free HTTPS** - No SSL certificate costs
✅ **Auto-renewal** - Certificates managed by Cloudflare
✅ **DDoS Protection** - Cloudflare's network protects your VPS
✅ **No Port Forwarding** - Works behind NAT/firewall
✅ **Fast Setup** - ~10 minutes from start to finish
✅ **Easy Management** - Simple systemctl commands

---

## Security Notes

🔒 **Encrypted connection** from Claude → Cloudflare → Your VPS
🔒 **No exposed ports** - Tunnel establishes outbound connection only
🔒 **Rate limiting** - Cloudflare provides automatic protection
🔒 **Access control** - Can add Cloudflare Access for additional auth

---

## Next Steps After Setup

1. ✅ Verify HTTPS endpoint works: `curl https://mcp.baliluxurystays.com/health`
2. ✅ Configure Claude MCP connector
3. ✅ Test MCP tools from Claude
4. ✅ Monitor tunnel logs for any issues
5. ✅ (Optional) Set up Cloudflare Access for additional authentication

---

## Support

- **Cloudflare Tunnel Docs:** https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- **Check tunnel status:** `systemctl status cloudflared`
- **View logs:** `journalctl -u cloudflared -f`

---

**Your MCP server will be available at:**
### 🔗 https://mcp.baliluxurystays.com

Ready to start? Follow Step 1 above! 🚀
