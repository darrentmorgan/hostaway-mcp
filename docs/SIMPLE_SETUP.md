# Simple MCP Server Setup (Direct Access)

**Status**: ✅ Server deployed and accessible on Hostinger VPS
**Decision**: Using direct IP access (skipping Cloudflare Tunnel complexity)

---

## Server Information

**Base URL**: `http://72.60.233.157:8080`
**Status**: HEALTHY (uptime: 235+ hours)

### Available Endpoints

- **Health Check**: http://72.60.233.157:8080/health
- **API Documentation**: http://72.60.233.157:8080/docs
- **OpenAPI Schema**: http://72.60.233.157:8080/openapi.json
- **Root**: http://72.60.233.157:8080/

---

## Using with Claude Desktop

### Configuration File Location

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

### Configuration (With API Key) ✅ RECOMMENDED

**Your Production API Key**: `mcp_x64EA0rh4EPmDsi8tVy-xzomCFTV1rApJmQdXGE-j00`

```json
{
  "mcpServers": {
    "hostaway": {
      "command": "/Users/darrenmorgan/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/darrenmorgan/AI_Projects/hostaway-mcp",
        "run",
        "python",
        "mcp_stdio_server.py"
      ],
      "env": {
        "REMOTE_MCP_URL": "http://72.60.233.157:8080",
        "REMOTE_MCP_API_KEY": "mcp_x64EA0rh4EPmDsi8tVy-xzomCFTV1rApJmQdXGE-j00"
      }
    }
  }
}
```

**How it works**:
- Uses native MCP stdio server (`mcp_stdio_server.py`)
- Connects to remote HTTP API at http://72.60.233.157:8080
- Authenticates with `X-API-Key` header
- Exposes 7 Hostaway tools to Claude

**Organization**: Baliluxurystays Organization (ID: 1)
**Status**: ✅ Verified Working (2025-10-29)

---

## Testing the Connection

### 1. Health Check (Browser or Terminal)

Open in browser: http://72.60.233.157:8080/health

Or via terminal:
```bash
curl http://72.60.233.157:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-29T04:00:22.505511+00:00",
  "version": "0.1.0",
  "service": "hostaway-mcp"
}
```

### 2. API Documentation (Browser)

Open: http://72.60.233.157:8080/docs

This shows all available endpoints with interactive testing.

### 3. Test with Claude Desktop

1. Add the configuration to your `claude_desktop_config.json`
2. Restart Claude Desktop completely (quit and reopen)
3. Start a new conversation
4. Type: "What MCP tools are available?"
5. Claude should list the Hostaway tools

---

## Advantages of Direct Access

✅ **Simple**: No complex tunnel configuration
✅ **Fast**: Direct connection, no extra hops
✅ **Debuggable**: Easy to test with curl/browser
✅ **No Dependencies**: Works without Cloudflare account

## Disadvantages

❌ **No HTTPS**: HTTP only (fine for personal use, not for production)
❌ **Exposed IP**: Server IP is visible to clients
❌ **No WAF**: No web application firewall or DDoS protection
❌ **No Custom Domain**: Must use IP address

---

## Production Upgrade Path

When you're ready to make this production-grade:

1. **Setup Cloudflare Tunnel** (we already started this)
2. **Get HTTPS**: Automatic SSL certificate
3. **Custom Domain**: `mcp.baliluxurystays.com`
4. **Security**: WAF, rate limiting, DDoS protection
5. **Hide Origin**: Cloudflare proxies requests

See `docs/CLOUDFLARE_TUNNEL_SETUP.md` for full tunnel setup.

---

## Troubleshooting

### Connection Refused

**Problem**: Can't connect to server

**Solution**:
```bash
# SSH into VPS
ssh root@72.60.233.157

# Check if Docker container is running
docker ps | grep hostaway-mcp

# If not running, start it
docker start hostaway-mcp

# Or restart it
docker restart hostaway-mcp

# Check logs
docker logs hostaway-mcp -f
```

### Firewall Blocking Port 8080

**Problem**: Connection times out

**Solution**:
```bash
# SSH into VPS
ssh root@72.60.233.157

# Check if port 8080 is open
sudo ufw status

# If needed, allow port 8080
sudo ufw allow 8080/tcp
sudo ufw reload
```

### Server Not Responding

**Check server health**:
```bash
ssh root@72.60.233.157
curl http://localhost:8080/health
```

If this works but external access doesn't, it's a firewall issue.

If this doesn't work, check Docker logs:
```bash
docker logs hostaway-mcp --tail 50
```

---

## Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| VPS Server | ✅ Running | Hostinger (72.60.233.157) |
| Docker Container | ✅ Healthy | Port 8080 |
| MCP Server | ✅ Responsive | FastAPI + MCP integration |
| Direct HTTP Access | ✅ Working | http://72.60.233.157:8080 |
| Cloudflare Tunnel | ⏸️ Optional | Can enable later for production |

---

## Next Steps

1. **Configure Claude Desktop** with the URL above
2. **Test the connection** by asking Claude to use MCP tools
3. **Explore API docs** at http://72.60.233.157:8080/docs
4. **Monitor logs** via `docker logs hostaway-mcp -f` (on VPS)

---

## Quick Reference Commands

```bash
# Test health
curl http://72.60.233.157:8080/health

# View API docs (browser)
open http://72.60.233.157:8080/docs

# SSH to server
ssh root@72.60.233.157

# View container logs
ssh root@72.60.233.157 "docker logs hostaway-mcp -f"

# Restart container
ssh root@72.60.233.157 "docker restart hostaway-mcp"
```

---

**Ready to use!** 🚀

Configure Claude Desktop with the URL and start using your Hostaway MCP tools.
