# MCP Connector Setup Guide

## Problem Summary

### Issue 1: Vercel Deployment Confusion ✅ FIXED
- **What happened:** Root `vercel.json` caused root directory to be linked to Vercel
- **Result:** Created wrong "hostaway-mcp" Vercel project
- **Fixed:**
  - Deleted incorrect Vercel project
  - Removed root `vercel.json`
  - Unlinked root from Vercel
  - Dashboard project remains correctly deployed at https://dashboard-iota-eight-75.vercel.app

### Issue 2: HTTPS Required for MCP Connector
- **Problem:** Claude requires HTTPS for remote MCP connectors
- **Current:** Your server runs on HTTP at `http://72.60.233.157:8080`
- **Need:** HTTPS endpoint

---

## 3 Solutions for HTTPS

### Option A: Cloudflare Tunnel (⭐ Recommended - Free & Easy)

**Pros:**
- ✅ Free HTTPS
- ✅ No certificate management
- ✅ DDoS protection
- ✅ Easy setup

**Setup:**
1. Follow: `./scripts/setup-cloudflare-tunnel.sh`
2. Get a domain (or subdomain from Cloudflare)
3. Tunnel automatically provides HTTPS

**Claude Connector Config:**
```
Name: Hostaway MCP
URL: https://mcp.yourdomain.com
OAuth Client ID: (empty)
OAuth Client Secret: (empty)
```

---

### Option B: Nginx + Let's Encrypt (Traditional HTTPS)

**Pros:**
- ✅ Full control
- ✅ Industry standard
- ✅ Free SSL certificates

**Cons:**
- ❌ Requires domain name
- ❌ Certificate renewal management
- ❌ More complex setup

**Setup:**
```bash
# On Hostinger VPS
cd /opt/hostaway-mcp
./scripts/setup-https-nginx.sh yourdomain.com your@email.com

# Deploy with nginx
docker compose -f docker-compose.prod.yml up -d
```

**Claude Connector Config:**
```
Name: Hostaway MCP
URL: https://yourdomain.com
OAuth Client ID: (empty)
OAuth Client Secret: (empty)
```

---

### Option C: Local MCP Server (Easiest for Testing)

**Pros:**
- ✅ No HTTPS needed
- ✅ Fastest setup
- ✅ No domain required

**Cons:**
- ❌ Only works on your local machine
- ❌ No remote access

**Setup:**
1. Copy `claude_desktop_config.json` to `~/.config/Claude/claude_desktop_config.json`
2. Update with your actual credentials
3. Restart Claude Desktop

**No custom connector needed** - uses built-in stdio MCP protocol

---

## Current Deployment Architecture

```
┌─────────────────────────────────────┐
│  Dashboard (Next.js)                │
│  https://dashboard-iota-eight-75... │ ✅ Working on Vercel
│  - UI for API key management        │
│  - Usage tracking dashboard         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  MCP Server (FastAPI)               │
│  http://72.60.233.157:8080          │ ⚠️ Needs HTTPS for Claude
│  - Hostaway integration             │
│  - MCP protocol endpoints           │
└─────────────────────────────────────┘
```

---

## Authentication Note

**IMPORTANT:** Don't put API keys in OAuth fields!

Your MCP server uses **API key authentication**, not OAuth:
- API keys are generated in the dashboard
- Passed via `X-API-Key` header
- OAuth fields in connector should be **empty**

---

## Next Steps

1. **Choose one option above**
2. **For remote (Option A or B):**
   - Set up HTTPS
   - Use custom connector with HTTPS URL
   - Leave OAuth fields empty

3. **For local (Option C):**
   - Configure Claude Desktop config
   - No custom connector needed
   - Works immediately for testing

---

## Files Created

- `scripts/setup-cloudflare-tunnel.sh` - Cloudflare setup guide
- `scripts/setup-https-nginx.sh` - Nginx + Let's Encrypt setup
- `nginx.conf` - Nginx reverse proxy configuration
- `docker-compose.prod.yml` - Updated with nginx + certbot services
- `claude_desktop_config.json` - Local MCP configuration template

---

## Recommended Path

1. **For production:** Use **Option A (Cloudflare Tunnel)**
   - Easiest and most secure
   - Free HTTPS
   - No certificate management

2. **For testing:** Use **Option C (Local)**
   - Fastest to set up
   - Good for development

3. **For self-hosted:** Use **Option B (Nginx)**
   - If you prefer traditional setup
   - Full control over infrastructure
