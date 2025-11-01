# Cloudflare Tunnel Setup (Keep Hostinger DNS)
## For mcp.baliluxurystays.com

**This guide lets you use Cloudflare Tunnel WITHOUT changing your Hostinger nameservers!**

You'll just add **ONE CNAME record** at Hostinger.

---

## What You Need

✅ Free Cloudflare account (no domain needed)
✅ SSH access to Hostinger VPS: `72.60.233.157`
✅ Access to Hostinger DNS settings

**Time:** ~15 minutes
**Cost:** $0 (completely free)

---

## Quick Setup (3 Steps)

### Step 1: Run Setup Script on VPS

**Copy script to VPS:**
```bash
scp scripts/setup-cloudflare-tunnel-manual-dns.sh root@72.60.233.157:/root/
```

**SSH into VPS:**
```bash
ssh root@72.60.233.157
```

**Run the script:**
```bash
bash /root/setup-cloudflare-tunnel-manual-dns.sh
```

**What happens:**
- Installs cloudflared
- Opens browser for Cloudflare login (free account)
- Creates tunnel
- Starts tunnel service
- **Gives you a tunnel hostname** like: `abc123.cfargotunnel.com`

**⚠️ IMPORTANT:** Copy the tunnel hostname from the output!

---

### Step 2: Add CNAME Record at Hostinger

The script will show you exactly what to add:

```
Type:   CNAME
Name:   mcp
Target: <tunnel-id>.cfargotunnel.com  (from script output)
TTL:    300
```

**Where to add it:**

1. Go to **Hostinger Control Panel** (https://hpanel.hostinger.com/)
2. Navigate to: **Domains** → **baliluxurystays.com** → **DNS / Name Servers**
3. Click **Add Record** or **Manage DNS Records**
4. Select **CNAME**
5. Enter:
   - **Name:** `mcp`
   - **Points to:** `<tunnel-id>.cfargotunnel.com`
   - **TTL:** `300`
6. **Save**

---

### Step 3: Test HTTPS Endpoint

Wait **1-5 minutes** for DNS propagation, then:

```bash
curl https://mcp.baliluxurystays.com/health
```

**Expected response:**
```json
{"status": "healthy"}
```

✅ **Success!** Your MCP server has HTTPS!

---

## Configure Claude MCP Connector

Now you can add the custom connector in Claude:

```
Name: Hostaway MCP
Remote MCP server: https://mcp.baliluxurystays.com
OAuth Client ID: (leave empty)
OAuth Client Secret: (leave empty)
```

Click **Add** and confirm trust.

---

## Architecture

```
Claude Desktop
    ↓ HTTPS
    ↓
mcp.baliluxurystays.com (CNAME → tunnel.cfargotunnel.com)
    ↓
Cloudflare Network (HTTPS/TLS handling)
    ↓ Encrypted Tunnel
    ↓
Hostinger VPS (72.60.233.157)
  ├─ cloudflared (tunnel client)
  └─ Docker: hostaway-mcp (port 8080)
```

---

## Benefits

✅ **Keep Hostinger nameservers** - No DNS migration
✅ **Free HTTPS** - Cloudflare handles SSL/TLS
✅ **No certificate management** - Auto-renewal
✅ **DDoS protection** - Cloudflare network
✅ **Simple setup** - Just one CNAME record

---

## Management

### Check Tunnel Status
```bash
sudo systemctl status cloudflared
```

### View Logs
```bash
sudo journalctl -u cloudflared -f
```

### Restart Tunnel
```bash
sudo systemctl restart cloudflared
```

### List Tunnels
```bash
cloudflared tunnel list
```

---

## Troubleshooting

### DNS not resolving?

Check the CNAME record:
```bash
dig mcp.baliluxurystays.com CNAME
```

Should show the tunnel hostname.

### Tunnel not connecting?

1. Check service status: `systemctl status cloudflared`
2. View logs: `journalctl -u cloudflared -f`
3. Verify MCP server is running: `docker ps`

### 502 Bad Gateway?

MCP server might not be running:
```bash
cd /opt/hostaway-mcp
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml up -d
```

---

## Summary

1. ✅ Run script on VPS → Get tunnel hostname
2. ✅ Add CNAME at Hostinger → Point to tunnel
3. ✅ Test HTTPS endpoint → Should work!
4. ✅ Configure Claude connector → Done!

**No nameserver changes required!** 🎉

---

## Ready?

Start with **Step 1** above and you'll have HTTPS in ~15 minutes!
