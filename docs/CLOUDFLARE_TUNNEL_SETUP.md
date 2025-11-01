# Cloudflare Tunnel Setup Guide

**Last Updated**: 2025-10-29
**Status**: Troubleshooting SSL handshake failure

## Current Issue

After migrating the Cloudflare Tunnel from locally-configured to dashboard-managed, the endpoint `https://mcp.baliluxurystays.com` is not accessible.

### Symptoms
- ✅ DNS resolves correctly: `mcp.baliluxurystays.com` → `5f107579-fe2f-4851-8707-34d97f1ef6e9.cfargotunnel.com`
- ✅ Cloudflare Tunnel daemon is connected (4 edge connections)
- ✅ MCP Docker container is healthy (responds on `localhost:8080`)
- ✅ Tunnel ingress rules are loaded correctly
- ❌ HTTPS endpoint returns SSL handshake failure
- ❌ No traffic reaching tunnel (zero activity in logs)

### Root Cause

The tunnel migration successfully transferred the **ingress rules** to the tunnel configuration but did **NOT** create the **Public Hostname** entry in Cloudflare Zero Trust dashboard.

Without the Public Hostname entry:
1. Cloudflare's edge servers don't route traffic for `mcp.baliluxurystays.com` to this tunnel
2. No SSL/TLS certificate is provisioned for the hostname
3. Connections fail with `SSL handshake failure`

## Verification

### 1. DNS Resolution (Working ✅)
```bash
dig +short mcp.baliluxurystays.com
# Output: 5f107579-fe2f-4851-8707-34d97f1ef6e9.cfargotunnel.com.
```

### 2. Tunnel Status (Working ✅)
```bash
ssh root@72.60.233.157 "systemctl status cloudflared"
# Output: active (running)
```

Cloudflared logs show:
```json
{
  "ingress": [
    {
      "hostname": "mcp.baliluxurystays.com",
      "originRequest": {},
      "service": "http://localhost:8080"
    },
    {
      "originRequest": {},
      "service": "http_status:404"
    }
  ],
  "warp-routing": {
    "enabled": false
  }
}
```

### 3. Local MCP Server (Working ✅)
```bash
curl http://localhost:8080/health
# Output: {"status":"healthy", ...}
```

### 4. SSL Connection (FAILING ❌)
```bash
curl -v https://mcp.baliluxurystays.com/health
# Output: SSL routines:ST_CONNECT:sslv3 alert handshake failure
```

## Solution: Add Public Hostname in Cloudflare Dashboard

### Step-by-Step Instructions

1. **Navigate to Cloudflare Zero Trust Dashboard**
   - Go to: https://one.dash.cloudflare.com/
   - Select your account
   - Click **Access** → **Tunnels**

2. **Select Your Tunnel**
   - Find tunnel: `5f107579-fe2f-4851-8707-34d97f1ef6e9`
   - Click on the tunnel name to open details

3. **Add Public Hostname**
   - Click the **Public Hostname** tab
   - Click **Add a public hostname** button

   Configure the hostname:
   - **Subdomain**: `mcp`
   - **Domain**: Select `baliluxurystays.com` from dropdown
   - **Path**: Leave blank
   - **Type**: `HTTP`
   - **URL**: `localhost:8080`

   Advanced settings (optional):
   - **TLS**: No TLS Verify (if using HTTP backend)
   - **No Happy Eyeballs**: Leave unchecked
   - **HTTP2 Connection**: Leave checked

   Click **Save hostname**

4. **Wait for Certificate Provisioning**
   - Cloudflare will automatically provision a TLS certificate
   - This usually takes 1-2 minutes
   - You can monitor progress in the dashboard

5. **Test the Endpoint**
   ```bash
   curl -v https://mcp.baliluxurystays.com/health
   ```

   Expected response:
   ```json
   {"status":"healthy","timestamp":"...","version":"0.1.0","service":"hostaway-mcp"}
   ```

## Alternative: Use Cloudflare Tunnel CLI

If you prefer command-line configuration:

```bash
# SSH into VPS
ssh root@72.60.233.157

# Add route to tunnel (requires Cloudflare API credentials)
cloudflared tunnel route dns \
  5f107579-fe2f-4851-8707-34d97f1ef6e9 \
  mcp.baliluxurystays.com
```

**Note**: This requires your Cloudflare account credentials and API token.

## Verification After Fix

### 1. Check DNS Propagation
```bash
dig +short mcp.baliluxurystays.com
# Should still show: 5f107579-fe2f-4851-8707-34d97f1ef6e9.cfargotunnel.com.
```

### 2. Test HTTPS Endpoint
```bash
curl https://mcp.baliluxurystays.com/health
# Should return: {"status":"healthy", ...}
```

### 3. Check Tunnel Logs
```bash
ssh root@72.60.233.157 "journalctl -u cloudflared -f"
# Should show incoming requests with 200 OK responses
```

### 4. Test MCP Tools
```bash
curl https://mcp.baliluxurystays.com/mcp/v1/tools
# Should return: List of available MCP tools
```

## Troubleshooting

### Issue: Still getting SSL errors after adding Public Hostname

**Possible causes**:
1. Certificate provisioning still in progress (wait 5 minutes)
2. DNS cache on your machine (flush DNS cache)
3. Browser cache (try incognito mode)

**Solutions**:
```bash
# Flush DNS cache (macOS)
sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder

# Test with curl (bypasses browser cache)
curl -v https://mcp.baliluxurystays.com/health

# Check certificate
openssl s_client -connect mcp.baliluxurystays.com:443 -servername mcp.baliluxurystays.com
```

### Issue: "Tunnel route not found" error in logs

**Solution**: The Public Hostname may not be saved correctly. Delete it and recreate.

### Issue: 404 Not Found from Cloudflare

**Possible cause**: The MCP server is not responding on `localhost:8080`

**Solution**:
```bash
# SSH into VPS
ssh root@72.60.233.157

# Check Docker container
docker ps | grep hostaway-mcp
docker logs hostaway-mcp

# Restart if needed
docker restart hostaway-mcp
```

## Technical Details

### Why Tunnel Migration Didn't Create Public Hostname

When you migrate a tunnel from locally-configured to dashboard-managed:
- ✅ **Ingress rules** are transferred to tunnel configuration
- ❌ **Public Hostnames** are NOT automatically created

This is by design - Cloudflare separates:
1. **Tunnel ingress rules** (internal routing within tunnel)
2. **Public Hostnames** (external routing at Cloudflare edge)

The migration only handles #1. You must manually configure #2 in the dashboard.

### Current Architecture

```
User Request (HTTPS)
    ↓
Cloudflare Edge (needs Public Hostname configuration ❌)
    ↓
Cloudflare Tunnel: 5f107579-fe2f-4851-8707-34d97f1ef6e9
    ↓
Ingress Rule: mcp.baliluxurystays.com → http://localhost:8080 ✅
    ↓
Docker Container: hostaway-mcp (port 8080) ✅
    ↓
FastAPI MCP Server ✅
```

## References

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Public Hostname Configuration](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/routing-to-tunnel/dns/)
- [Tunnel Migration Guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/)

## Current Status

**Next Action Required**: Add Public Hostname in Cloudflare Zero Trust dashboard (see Step 3 above).

Once configured, the endpoint will be accessible at:
- **Health Check**: https://mcp.baliluxurystays.com/health
- **API Docs**: https://mcp.baliluxurystays.com/docs
- **MCP Tools**: https://mcp.baliluxurystays.com/mcp/v1/tools
