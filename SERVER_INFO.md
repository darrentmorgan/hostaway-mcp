# Hostaway MCP Server - Production Info

## Server Details

- **Server**: `http://72.60.233.157:8080`
- **Location**: `/opt/hostaway-mcp/`
- **Service**: `hostaway-mcp.service` (systemd)
- **Status**: ✅ Running with database authentication

## API Key

Your active API key: `mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk`

## Quick Commands

```bash
# SSH into server
ssh -i ~/.ssh/id_ed25519_damorgs root@72.60.233.157

# Check service status
systemctl status hostaway-mcp

# View logs
tail -f /tmp/mcp-server.log

# Restart service
systemctl restart hostaway-mcp

# Stop service
systemctl stop hostaway-mcp

# Start service
systemctl start hostaway-mcp

# Test health endpoint
curl http://localhost:8080/health

# Test with API key
curl -H "X-API-Key: mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk" http://localhost:8080/health
```

## What Was Deployed

### Updated Files:
- `src/mcp/security.py` - **Database-backed API key authentication**
  - Validates keys against Supabase `api_keys` table
  - SHA-256 key hashing
  - Updates `last_used_at` timestamp
  - Multi-tenant organization isolation

### Environment Variables Added:
```bash
SUPABASE_URL=https://iixikajovibmfvinkwex.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci...
```

### Virtual Environment:
- Location: `/opt/hostaway-mcp/venv/`
- Python: 3.12
- Dependencies: All installed from pyproject.toml

## Features

✅ **Database Authentication**: API keys validated against Supabase
✅ **Auto-Restart**: Systemd service automatically restarts on failure
✅ **Boot Persistence**: Service starts automatically on server reboot
✅ **Multi-Tenant**: Organization-level isolation via `request.state`
✅ **Usage Tracking**: `last_used_at` timestamp updated on each request

## Next Steps

1. **Restart Claude Desktop** completely
2. **Test MCP connection** - The server should now connect successfully
3. **Verify in Dashboard** - Check that `last_used_at` updates when you use the MCP

## Troubleshooting

### Server won't start:
```bash
# Check logs
sudo journalctl -u hostaway-mcp -n 50

# Check manual logs
tail -100 /tmp/mcp-server.log
```

### API key not working:
```bash
# Verify environment variables
cat /opt/hostaway-mcp/.env | grep SUPABASE

# Test Supabase connection
ssh root@72.60.233.157
cd /opt/hostaway-mcp
source venv/bin/activate
python3 -c "from supabase import create_client; import os; print('OK')"
```

### Port not accessible:
```bash
# Check firewall
sudo ufw status

# Check if port is listening
sudo netstat -tlnp | grep 8080
```

## Deployment Date

2025-10-14 20:50 UTC

## Version

hostaway-mcp v0.1.0
