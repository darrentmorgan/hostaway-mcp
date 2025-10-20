# Hostinger VPS Deployment Guide - Hostaway MCP Server

**Target**: Deploy Hostaway MCP Server to Hostinger VPS
**Date**: 2025-10-12
**Status**: Ready for deployment
**Compatibility**: ✅ Fully compatible with Hostinger's MCP infrastructure

---

## 🎯 Deployment Overview

### What We Have
- **Framework**: FastAPI with FastAPI-MCP integration
- **Containerization**: Docker + Docker Compose
- **MCP Transport**: HTTP/SSE via ASGI
- **Current Port**: 8000
- **MCP Endpoint**: `/mcp` (already configured)
- **Health Check**: `/health` endpoint
- **Status**: Production-ready (v1.0, Grade A-)

### What Hostinger Needs
- **VPS**: Ubuntu 24 with Docker support
- **Port**: 8080 (requires config change)
- **Access**: Web URL (e.g., `http://your-app.hstgr.cloud:8080/mcp`)
- **Protocol**: MCP over HTTP/SSE (✅ we already have this)

### Compatibility Assessment
✅ **Fully Compatible** - Our FastAPI-MCP setup matches Hostinger's infrastructure
⚠️ **Minor Changes Needed**: Port change (8000 → 8080)

---

## 📋 Prerequisites

### 1. Hostinger VPS Setup
- [ ] Provision Ubuntu 24 VPS from Hostinger
- [ ] Enable Docker support in VPS settings
- [ ] Note your VPS domain (e.g., `your-app.hstgr.cloud`)
- [ ] Ensure port 8080 is open in firewall

### 2. Local Prerequisites
- [ ] SSH key for VPS access
- [ ] Hostaway API credentials (ACCOUNT_ID, SECRET_KEY)
- [ ] Docker installed locally (for testing changes)

### 3. VPS Access
```bash
# SSH into Hostinger VPS
ssh root@your-app.hstgr.cloud

# Or use provided SSH credentials
ssh -i ~/.ssh/hostinger_key root@your-server-ip
```

---

## 🔧 Configuration Changes Required

### Change 1: Update Port to 8080

**File**: `docker-compose.yml`
```yaml
services:
  hostaway-mcp:
    ports:
      - "8080:8080"  # Changed from 8000:8000
```

**File**: `Dockerfile` (CMD line)
```dockerfile
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
# Changed from --port 8000
```

### Change 2: Create Production Docker Compose

**File**: `docker-compose.prod.yml` (new file)
```yaml
services:
  hostaway-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hostaway-mcp-server
    ports:
      - "8080:8080"
    environment:
      # Hostaway API (set on VPS)
      - HOSTAWAY_ACCOUNT_ID=${HOSTAWAY_ACCOUNT_ID}
      - HOSTAWAY_SECRET_KEY=${HOSTAWAY_SECRET_KEY}
      - HOSTAWAY_API_BASE_URL=https://api.hostaway.com/v1

      # Production settings
      - LOG_LEVEL=INFO
      - ENVIRONMENT=production
      - RATE_LIMIT_IP=15
      - RATE_LIMIT_ACCOUNT=20
      - MAX_CONCURRENT_REQUESTS=100
    restart: always
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8080/health', timeout=5.0).raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge
```

### Change 3: Update CORS for Production

**File**: `src/api/main.py` (line 89)
```python
# Update CORS origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://claude.ai",
        "https://www.anthropic.com",
        "*"  # Remove in strict production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚀 Deployment Steps

### Step 1: Prepare Application for Deployment

```bash
# 1. Update port configuration
# Edit docker-compose.prod.yml (use changes above)

# 2. Test locally with new port
docker compose -f docker-compose.prod.yml up --build

# 3. Verify MCP endpoint
curl http://localhost:8080/mcp
# Should return MCP protocol response

# 4. Verify health check
curl http://localhost:8080/health
# Should return: {"status": "healthy", ...}

# 5. Stop local test
docker compose -f docker-compose.prod.yml down
```

### Step 2: Transfer Files to Hostinger VPS

```bash
# Method A: Git Clone (Recommended)
ssh root@your-app.hstgr.cloud
cd /opt
git clone https://github.com/yourusername/hostaway-mcp.git
cd hostaway-mcp

# Method B: SCP Transfer
scp -r /Users/darrenmorgan/AI_Projects/hostaway-mcp root@your-app.hstgr.cloud:/opt/

# Method C: rsync (Best for updates)
rsync -avz --exclude '.venv' --exclude 'logs' \
  /Users/darrenmorgan/AI_Projects/hostaway-mcp/ \
  root@your-app.hstgr.cloud:/opt/hostaway-mcp/
```

### Step 3: Configure Environment on VPS

```bash
# SSH into VPS
ssh root@your-app.hstgr.cloud

# Navigate to app directory
cd /opt/hostaway-mcp

# Create .env file with production credentials
cat > .env << 'EOF'
HOSTAWAY_ACCOUNT_ID=your_actual_account_id
HOSTAWAY_SECRET_KEY=your_actual_secret_key
HOSTAWAY_API_BASE_URL=https://api.hostaway.com/v1
LOG_LEVEL=INFO
ENVIRONMENT=production
RATE_LIMIT_IP=15
RATE_LIMIT_ACCOUNT=20
MAX_CONCURRENT_REQUESTS=100
EOF

# Secure the .env file
chmod 600 .env
```

### Step 4: Install Docker on VPS (if not installed)

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### Step 5: Deploy Application

```bash
# Navigate to app directory
cd /opt/hostaway-mcp

# Build and start the container
docker compose -f docker-compose.prod.yml up -d --build

# Check container status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f hostaway-mcp

# Verify health
curl http://localhost:8080/health
```

### Step 6: Configure Firewall (if needed)

```bash
# Allow port 8080
ufw allow 8080/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

---

## 🔌 MCP Client Configuration

### For Claude Desktop

**File**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "hostaway-mcp": {
      "url": "http://your-app.hstgr.cloud:8080/mcp",
      "description": "Hostaway property management MCP server"
    }
  }
}
```

### For Cursor IDE

**File**: `.cursor/mcp_config.json`

```json
{
  "mcpServers": {
    "hostaway-mcp": {
      "url": "http://your-app.hstgr.cloud:8080/mcp",
      "description": "Remote Hostaway MCP server"
    }
  }
}
```

### Test Connection

```bash
# From your local machine
curl http://your-app.hstgr.cloud:8080/health

# Test MCP endpoint
curl http://your-app.hstgr.cloud:8080/mcp
```

---

## 📊 Verification Checklist

### Deployment Verification
- [ ] Container is running: `docker compose -f docker-compose.prod.yml ps`
- [ ] Health check passes: `curl http://localhost:8080/health`
- [ ] MCP endpoint accessible: `curl http://localhost:8080/mcp`
- [ ] Logs show no errors: `docker compose logs`
- [ ] All 9 MCP tools discoverable

### Networking Verification
- [ ] External access works: `curl http://your-app.hstgr.cloud:8080/health`
- [ ] Port 8080 is open in firewall
- [ ] CORS headers present in responses
- [ ] Correlation IDs in response headers

### Authentication Verification
- [ ] OAuth token acquisition successful (check logs)
- [ ] Token refresh works (check logs after 24h)
- [ ] Rate limiting enforced (test with burst requests)

### MCP Integration Verification
- [ ] Claude Desktop can connect to URL
- [ ] All 9 tools appear in Claude Desktop
- [ ] Test tools return Hostaway data:
  - `list_properties` - should return properties
  - `get_property_details` - should return details
  - `search_bookings` - should return bookings

---

## 🔄 Update & Maintenance

### Updating the Application

```bash
# SSH into VPS
ssh root@your-app.hstgr.cloud

# Navigate to app
cd /opt/hostaway-mcp

# Pull latest changes (if using Git)
git pull origin main

# Or sync changes (if using rsync)
# Run from local machine:
rsync -avz --exclude '.venv' --exclude 'logs' \
  /Users/darrenmorgan/AI_Projects/hostaway-mcp/ \
  root@your-app.hstgr.cloud:/opt/hostaway-mcp/

# Rebuild and restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build

# Verify
docker compose -f docker-compose.prod.yml logs -f
```

### Monitoring

```bash
# View real-time logs
docker compose -f docker-compose.prod.yml logs -f

# Check container health
docker compose -f docker-compose.prod.yml ps

# View container stats
docker stats hostaway-mcp-server

# Check disk usage
df -h
du -sh /opt/hostaway-mcp
```

### Backup

```bash
# Backup environment file
cp .env .env.backup

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# Create full backup
tar -czf hostaway-mcp-backup-$(date +%Y%m%d).tar.gz \
  --exclude='.venv' \
  --exclude='logs' \
  /opt/hostaway-mcp
```

---

## 🛠️ Troubleshooting

### Issue: Container Fails to Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Common causes:
# 1. Missing .env file
cat .env  # Verify exists and has correct values

# 2. Port already in use
netstat -tulpn | grep 8080
# Kill process using port if needed

# 3. Build errors
docker compose -f docker-compose.prod.yml build --no-cache
```

### Issue: MCP Endpoint Not Accessible

```bash
# 1. Verify container is running
docker compose -f docker-compose.prod.yml ps

# 2. Check if port is listening
netstat -tulpn | grep 8080

# 3. Test from inside container
docker exec -it hostaway-mcp-server curl http://localhost:8080/health

# 4. Check firewall
ufw status
ufw allow 8080/tcp
```

### Issue: Authentication Failures

```bash
# 1. Verify credentials in .env
cat .env | grep HOSTAWAY

# 2. Check logs for OAuth errors
docker compose -f docker-compose.prod.yml logs | grep -i auth

# 3. Test credentials manually
docker exec -it hostaway-mcp-server python -c "
from src.mcp.config import HostawayConfig
config = HostawayConfig()
print(f'Account ID: {config.account_id[:8]}...')
"
```

### Issue: High Memory Usage

```bash
# Check container stats
docker stats hostaway-mcp-server

# Restart container
docker compose -f docker-compose.prod.yml restart

# Limit resources (add to docker-compose.prod.yml)
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '1'
      memory: 512M
```

---

## 🔐 Security Best Practices

### Production Security Checklist
- [ ] Use HTTPS (configure reverse proxy)
- [ ] Restrict CORS to known origins
- [ ] Enable firewall (ufw)
- [ ] Use secrets manager for credentials
- [ ] Regular security updates: `apt update && apt upgrade`
- [ ] Monitor logs for suspicious activity
- [ ] Implement rate limiting (already done)
- [ ] Use non-root user in container (already done)

### HTTPS Setup (Optional, Recommended)

```bash
# Install Nginx
apt install nginx certbot python3-certbot-nginx -y

# Create Nginx config
cat > /etc/nginx/sites-available/hostaway-mcp << 'EOF'
server {
    listen 80;
    server_name your-app.hstgr.cloud;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/hostaway-mcp /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# Get SSL certificate
certbot --nginx -d your-app.hstgr.cloud
```

---

## 📈 Next Steps After Deployment

1. **✅ Verify Deployment**
   - Test all 9 MCP tools from Claude Desktop
   - Monitor logs for first 24 hours
   - Verify OAuth token refresh (after 7 days)

2. **🔧 Optional Enhancements**
   - Set up HTTPS with Let's Encrypt
   - Configure monitoring (Prometheus + Grafana)
   - Set up automated backups
   - Configure log rotation

3. **📊 Monitoring Setup**
   - Add uptime monitoring (UptimeRobot, Pingdom)
   - Set up alerting (email, Slack)
   - Configure error tracking (Sentry)

4. **🚀 Scale for Production**
   - Add load balancer if needed
   - Configure auto-scaling (if traffic increases)
   - Set up CDN (Cloudflare) for static assets

---

## 📝 Quick Reference

### Useful Commands

```bash
# Start server
docker compose -f docker-compose.prod.yml up -d

# Stop server
docker compose -f docker-compose.prod.yml down

# Restart server
docker compose -f docker-compose.prod.yml restart

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Rebuild
docker compose -f docker-compose.prod.yml up -d --build

# Shell access
docker exec -it hostaway-mcp-server /bin/sh

# Health check
curl http://localhost:8080/health
```

### Important Endpoints

- **Health Check**: `http://your-app.hstgr.cloud:8080/health`
- **MCP Endpoint**: `http://your-app.hstgr.cloud:8080/mcp`
- **API Docs**: `http://your-app.hstgr.cloud:8080/docs`
- **OpenAPI Schema**: `http://your-app.hstgr.cloud:8080/openapi.json`

### MCP Tools Available

1. `authenticate` - OAuth authentication
2. `refresh_token` - Token refresh
3. `list_properties` - List all properties
4. `get_property_details` - Property details
5. `check_availability` - Calendar availability
6. `search_bookings` - Search bookings
7. `get_booking_details` - Booking details
8. `get_guest_info` - Guest information
9. `get_financial_reports` - Financial reports

---

## ✅ Deployment Status

**Pre-Deployment**: ⏳ Ready to deploy
**Deployment**: ⏸️ Pending VPS provisioning
**Post-Deployment**: ⏸️ Pending verification

**Next Action**:
1. Provision Ubuntu 24 VPS on Hostinger
2. Apply configuration changes (port 8080)
3. Deploy using steps above
4. Configure MCP clients to use production URL

---

**Support**: For issues, refer to DEBUG_SUMMARY.md and PRODUCTION_READINESS_REPORT.md
