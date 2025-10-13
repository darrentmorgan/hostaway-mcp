# Hostinger Deployment - Quick Start Guide

**🚀 Deploy in 5 Minutes**

This guide will get your Hostaway MCP Server running on Hostinger VPS in just a few steps.

---

## Prerequisites

1. **Hostinger VPS**: Ubuntu 24 VPS provisioned
2. **SSH Access**: You can connect via `ssh root@your-vps-hostname`
3. **Credentials**: Your Hostaway Account ID and Secret Key

---

## Option 1: Automated Deployment (Recommended)

### Step 1: Run Deployment Script

```bash
# From your local machine, in the project directory
./deploy.sh root@your-app.hstgr.cloud
```

The script will:
- ✅ Sync files to VPS
- ✅ Install Docker (if needed)
- ✅ Create .env template
- ✅ Build and deploy container
- ✅ Configure firewall
- ✅ Verify deployment

### Step 2: Configure Credentials

```bash
# SSH into VPS
ssh root@your-app.hstgr.cloud

# Edit .env file
nano /opt/hostaway-mcp/.env

# Update these values:
HOSTAWAY_ACCOUNT_ID=your_actual_account_id
HOSTAWAY_SECRET_KEY=your_actual_secret_key
```

Save and exit (Ctrl+X, Y, Enter)

### Step 3: Restart Application

```bash
cd /opt/hostaway-mcp
docker compose -f docker-compose.prod.yml restart
```

### Step 4: Verify Deployment

```bash
# Check health
curl http://localhost:8080/health

# Get your public IP
curl -s ifconfig.me

# Test MCP endpoint
curl http://$(curl -s ifconfig.me):8080/mcp
```

**Done!** 🎉

---

## Option 2: Manual Deployment

### Step 1: Transfer Files

```bash
# From local machine
rsync -avz --exclude '.venv' --exclude 'logs' \
  /Users/darrenmorgan/AI_Projects/hostaway-mcp/ \
  root@your-app.hstgr.cloud:/opt/hostaway-mcp/
```

### Step 2: Install Docker on VPS

```bash
# SSH into VPS
ssh root@your-app.hstgr.cloud

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y
```

### Step 3: Configure Environment

```bash
cd /opt/hostaway-mcp

# Create .env file
cat > .env << 'EOF'
HOSTAWAY_ACCOUNT_ID=your_account_id
HOSTAWAY_SECRET_KEY=your_secret_key
HOSTAWAY_API_BASE_URL=https://api.hostaway.com/v1
LOG_LEVEL=INFO
ENVIRONMENT=production
EOF

# Secure the file
chmod 600 .env
```

### Step 4: Deploy Container

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 5: Configure Firewall

```bash
ufw allow 8080/tcp
ufw enable
```

### Step 6: Verify

```bash
# Check status
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f
```

---

## Configure MCP Clients

### Claude Desktop

**File**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "hostaway-mcp": {
      "url": "http://YOUR_VPS_IP:8080/mcp",
      "description": "Remote Hostaway MCP server on Hostinger"
    }
  }
}

Replace `YOUR_VPS_IP` with your actual VPS IP address:
```bash
# Get VPS IP
ssh root@your-app.hstgr.cloud 'curl -s ifconfig.me'
```

### Test Connection

1. Restart Claude Desktop
2. Check MCP Servers settings → should see "hostaway-mcp" connected
3. Test: "Use hostaway-mcp to list my properties"

---

## Useful Commands

### Deployment Management

```bash
# Deploy/Update
./deploy.sh root@your-app.hstgr.cloud

# Manual restart
ssh root@your-app.hstgr.cloud 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml restart'

# View logs
ssh root@your-app.hstgr.cloud 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml logs -f'

# Stop server
ssh root@your-app.hstgr.cloud 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml down'
```

### Monitoring

```bash
# Check container status
ssh root@your-app.hstgr.cloud 'docker ps'

# Check container health
ssh root@your-app.hstgr.cloud 'docker inspect --format="{{.State.Health.Status}}" hostaway-mcp-server'

# View container stats
ssh root@your-app.hstgr.cloud 'docker stats hostaway-mcp-server'
```

### Troubleshooting

```bash
# View full logs
ssh root@your-app.hstgr.cloud 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml logs'

# Rebuild from scratch
ssh root@your-app.hstgr.cloud 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml up -d --build'

# Access container shell
ssh root@your-app.hstgr.cloud 'docker exec -it hostaway-mcp-server /bin/sh'
```

---

## Verify Deployment Checklist

- [ ] Container is running: `docker ps` shows "Up" status
- [ ] Health check passes: `curl http://localhost:8080/health` returns healthy
- [ ] MCP endpoint accessible: `curl http://localhost:8080/mcp` returns response
- [ ] External access works: `curl http://YOUR_VPS_IP:8080/health` from local machine
- [ ] Firewall allows port 8080: `ufw status` shows 8080/tcp allowed
- [ ] Claude Desktop connects: MCP server shows "connected" status
- [ ] Tools are available: Can see 9 MCP tools in Claude Desktop
- [ ] Authentication works: Test a tool like `list_properties`

---

## Common Issues

### Issue: Container won't start

```bash
# Check logs for errors
docker compose -f docker-compose.prod.yml logs

# Common fix: Rebuild without cache
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build --no-cache
```

### Issue: Can't connect from Claude Desktop

```bash
# 1. Check if port is open
ssh root@your-app.hstgr.cloud 'netstat -tulpn | grep 8080'

# 2. Verify external access
curl http://YOUR_VPS_IP:8080/health

# 3. Check firewall
ssh root@your-app.hstgr.cloud 'ufw status'
```

### Issue: Authentication fails

```bash
# 1. Verify credentials in .env
ssh root@your-app.hstgr.cloud 'cat /opt/hostaway-mcp/.env'

# 2. Check logs for OAuth errors
ssh root@your-app.hstgr.cloud 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml logs | grep -i auth'

# 3. Restart to pick up new credentials
ssh root@your-app.hstgr.cloud 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml restart'
```

---

## Next Steps

1. **Set Up HTTPS** (Optional but recommended)
   - See: HOSTINGER_DEPLOYMENT.md → HTTPS Setup section
   - Use Nginx + Let's Encrypt for SSL

2. **Configure Monitoring**
   - Set up uptime monitoring (UptimeRobot, Pingdom)
   - Configure alerts for downtime

3. **Backup Strategy**
   - Regular .env backups
   - Container configuration backups
   - Log rotation setup

4. **Performance Tuning**
   - Monitor resource usage
   - Adjust MAX_CONCURRENT_REQUESTS if needed
   - Consider caching layer (Redis)

---

## Support

- **Full Documentation**: See `HOSTINGER_DEPLOYMENT.md`
- **Troubleshooting**: See `DEBUG_SUMMARY.md`
- **Production Readiness**: See `PRODUCTION_READINESS_REPORT.md`

---

**🎉 You're Done!**

Your Hostaway MCP Server is now deployed on Hostinger and accessible remotely from Claude Desktop and other MCP clients.
