# Secure Deployment Guide - Hostaway MCP Server

**🔒 Production-Ready Deployment with API Key Authentication**

This guide walks you through deploying the Hostaway MCP Server with proper security measures.

---

## 🔐 Security Features

✅ **API Key Authentication** - MCP endpoint protected with secure API key
✅ **Encrypted Transport** - All communication over HTTPS (when configured)
✅ **Credential Protection** - Hostaway credentials stored securely in .env
✅ **Rate Limiting** - Built-in protection against abuse
✅ **Audit Logging** - All requests logged with correlation IDs

---

## 📋 Prerequisites

1. **VPS Access**: SSH access to `root@72.60.233.157`
2. **Credentials**: Hostaway Account ID and Secret Key
3. **API Key**: `f728931633a03fd4e099a27b1e7edddbe9da5b07eafdc88bd3e431538b565e44` (save this!)

---

## 🚀 Deployment Steps

### Step 1: Sync Security Files to VPS

From your **local terminal**:

```bash
cd /Users/darrenmorgan/AI_Projects/hostaway-mcp

rsync -avz --progress \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  --exclude='logs/' \
  --exclude='.env.local' \
  ./ root@72.60.233.157:/opt/hostaway-mcp/
```

### Step 2: Configure Environment with Security

SSH into VPS:

```bash
ssh root@72.60.233.157
cd /opt/hostaway-mcp
```

Create/update .env file:

```bash
nano .env
```

Add this configuration:

```bash
# Hostaway API Configuration
HOSTAWAY_ACCOUNT_ID=161051
HOSTAWAY_SECRET_KEY=***REMOVED***
HOSTAWAY_API_BASE_URL=https://api.hostaway.com/v1

# MCP Security - REQUIRED for production
MCP_API_KEY=f728931633a03fd4e099a27b1e7edddbe9da5b07eafdc88bd3e431538b565e44

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=production
RATE_LIMIT_IP=15
RATE_LIMIT_ACCOUNT=20
MAX_CONCURRENT_REQUESTS=100
```

Save and secure the file:

```bash
chmod 600 .env
```

### Step 3: Deploy Secured Application

```bash
# Still on VPS
cd /opt/hostaway-mcp

# Deploy with new security settings
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 4: Verify Security

**Test 1: Health check (unprotected, should work)**

```bash
curl http://localhost:8080/health
```

Expected: `{"status":"healthy",...}`

**Test 2: MCP endpoint without API key (should fail)**

```bash
curl http://localhost:8080/mcp
```

Expected: `{"detail":"Missing API key. Provide X-API-Key header."}`

**Test 3: MCP endpoint with API key (should work)**

```bash
curl -H "X-API-Key: f728931633a03fd4e099a27b1e7edddbe9da5b07eafdc88bd3e431538b565e44" \
  http://localhost:8080/mcp
```

Expected: MCP protocol response (JSON)

### Step 5: Configure Firewall

```bash
# Allow port 8080
ufw allow 8080/tcp

# Enable firewall
echo "y" | ufw enable

# Verify
ufw status
```

---

## 🖥️ Claude Desktop Configuration

### Update Claude Desktop Config

**File**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "hostaway-mcp": {
      "url": "http://72.60.233.157:8080/mcp",
      "headers": {
        "X-API-Key": "f728931633a03fd4e099a27b1e7edddbe9da5b07eafdc88bd3e431538b565e44"
      },
      "description": "Secure Hostaway MCP server on Hostinger"
    }
  }
}
```

**Important**: The API key is now required in the headers!

### Restart Claude Desktop

1. Quit Claude Desktop completely (Cmd+Q)
2. Reopen Claude Desktop
3. Check MCP Servers settings → "hostaway-mcp" should show as connected

### Test Connection

Ask Claude Desktop:

```
Use hostaway-mcp to list my properties
```

Expected: Claude should successfully authenticate and return your Hostaway properties

---

## 🔒 Security Verification Checklist

After deployment, verify these security measures:

- [ ] **MCP endpoint requires API key**: `curl http://72.60.233.157:8080/mcp` returns 401
- [ ] **Health check is public**: `curl http://72.60.233.157:8080/health` works
- [ ] **API key authentication works**: Request with `X-API-Key` header succeeds
- [ ] **Firewall is enabled**: `ufw status` shows active
- [ ] **Logs show authentication**: `docker logs` shows "API key authenticated successfully"
- [ ] **Claude Desktop connects**: MCP shows "connected" with green status

---

## 🛡️ Security Best Practices

### 1. API Key Management

**Rotate API Key Regularly**:

```bash
# Generate new API key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Update .env on VPS
ssh root@72.60.233.157 'nano /opt/hostaway-mcp/.env'

# Restart application
ssh root@72.60.233.157 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml restart'

# Update Claude Desktop config with new key
```

### 2. Credential Security

✅ **Never commit credentials** to git
✅ **.env file permissions**: Always `chmod 600 .env`
✅ **Use environment variables**: Never hardcode secrets
✅ **Rotate Hostaway credentials** periodically

### 3. Network Security

**Current Setup**: Port 8080 open to public

**Recommended Improvements**:

**Option A: IP Whitelist** (Quick)

```bash
# Remove public access
ufw delete allow 8080/tcp

# Allow only your IP
ufw allow from YOUR_HOME_IP to any port 8080

# Get your IP
curl ifconfig.me
```

**Option B: SSH Tunnel** (Most Secure)

```bash
# From local machine
ssh -L 8080:localhost:8080 root@72.60.233.157

# Use in Claude Desktop
{
  "url": "http://localhost:8080/mcp",
  "headers": {"X-API-Key": "..."}
}
```

**Option C: HTTPS with Nginx** (Production)

See `HOSTINGER_DEPLOYMENT.md` → HTTPS Setup section

### 4. Monitoring & Alerts

**View Authentication Logs**:

```bash
ssh root@72.60.233.157 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml logs | grep -i "api key"'
```

**Monitor Failed Authentication Attempts**:

```bash
ssh root@72.60.233.157 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml logs | grep -i "invalid api key"'
```

---

## 🔧 Troubleshooting

### Issue: 401 Unauthorized in Claude Desktop

**Cause**: Missing or incorrect API key

**Fix**:

1. Check Claude Desktop config has correct API key in headers
2. Verify API key matches .env file on VPS
3. Restart Claude Desktop after config change

```bash
# Verify API key on VPS
ssh root@72.60.233.157 'grep MCP_API_KEY /opt/hostaway-mcp/.env'
```

### Issue: MCP endpoint accessible without API key

**Cause**: MCP_API_KEY not set in .env

**Fix**:

```bash
ssh root@72.60.233.157
cd /opt/hostaway-mcp

# Add to .env
echo "MCP_API_KEY=f728931633a03fd4e099a27b1e7edddbe9da5b07eafdc88bd3e431538b565e44" >> .env

# Restart
docker compose -f docker-compose.prod.yml restart
```

### Issue: Container fails to start

**Check logs**:

```bash
ssh root@72.60.233.157 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml logs'
```

**Common fixes**:

1. Verify all required env vars in .env
2. Check file permissions: `chmod 600 .env`
3. Rebuild: `docker compose -f docker-compose.prod.yml up -d --build --no-cache`

---

## 📊 Security Monitoring

### Real-Time Log Monitoring

```bash
ssh root@72.60.233.157 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml logs -f'
```

### Audit Log Search

```bash
# Find all authentication attempts
ssh root@72.60.233.157 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml logs | grep "API key"'

# Find failed attempts
ssh root@72.60.233.157 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml logs | grep "Invalid API key"'

# Find successful authentications
ssh root@72.60.233.157 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml logs | grep "authenticated successfully"'
```

---

## 🔐 Post-Deployment Security

### 1. Change VPS Root Password

```bash
ssh root@72.60.233.157 'passwd'
```

### 2. Set Up SSH Key Authentication (Disable Password)

```bash
# From local machine
ssh-copy-id root@72.60.233.157

# On VPS, disable password auth
ssh root@72.60.233.157 'sed -i "s/#PasswordAuthentication yes/PasswordAuthentication no/" /etc/ssh/sshd_config && systemctl restart sshd'
```

### 3. Configure Log Rotation

```bash
ssh root@72.60.233.157 << 'EOF'
cat > /etc/logrotate.d/hostaway-mcp << 'LOGROTATE'
/opt/hostaway-mcp/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
}
LOGROTATE
EOF
```

---

## ✅ Deployment Complete!

Your Hostaway MCP Server is now:

✅ **Deployed** on Hostinger VPS
✅ **Secured** with API key authentication
✅ **Protected** by firewall
✅ **Monitored** with structured logging
✅ **Ready** for Claude Desktop integration

### Next Steps

1. ✅ Test all MCP tools in Claude Desktop
2. ✅ Monitor logs for first 24 hours
3. ✅ Set up HTTPS (optional, recommended)
4. ✅ Configure backup strategy
5. ✅ Document any custom configurations

---

**🎉 Congratulations!** Your secure MCP server is ready for production use!
