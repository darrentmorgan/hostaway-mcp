# Hostaway MCP Server - Deployment Guide

## Quick Deployment to Hostinger

### Step 1: Package the Code

Run this locally to create a deployment package:

```bash
cd /Users/darrenmorgan/AI_Projects/hostaway-mcp

# Create deployment package
tar -czf hostaway-mcp-deploy.tar.gz \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='dashboard' \
  --exclude='.next' \
  --exclude='node_modules' \
  --exclude='.env.local' \
  --exclude='tests' \
  src/ \
  pyproject.toml \
  mcp_stdio_server.py

echo "Package created: hostaway-mcp-deploy.tar.gz"
```

### Step 2: Upload to Hostinger

Upload `hostaway-mcp-deploy.tar.gz` to your Hostinger server at `/home/u631126255/hostaway-mcp/`

**Option A: Using SCP**
```bash
scp hostaway-mcp-deploy.tar.gz u631126255@72.60.233.157:/home/u631126255/hostaway-mcp/
```

**Option B: Using Hostinger File Manager**
- Login to Hostinger control panel
- Navigate to File Manager
- Go to `/home/u631126255/hostaway-mcp/`
- Upload the file

### Step 3: Deploy on Server

SSH into your Hostinger server:
```bash
ssh u631126255@72.60.233.157
```

Then run these commands:

```bash
cd /home/u631126255/hostaway-mcp

# Backup current version
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz src/ .env || true

# Extract new version
tar -xzf hostaway-mcp-deploy.tar.gz
rm hostaway-mcp-deploy.tar.gz

# Update .env with Supabase credentials
cat >> .env << 'EOF'

# Supabase Configuration (for API Key validation)
SUPABASE_URL=https://iixikajovibmfvinkwex.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlpeGlrYWpvdmlibWZ2aW5rd2V4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNjg3MDY5NCwiZXhwIjoyMDUyNDQ2Njk0fQ.VCcTWbWE-3Hfi5UaNz4A4yEqqqJdEd3l4sEfhKBBHIg
EOF

# Stop existing MCP server
pkill -f "uvicorn.*main:app" || true
pkill -f "python.*mcp" || true

# Start MCP server
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080 > /tmp/mcp-server.log 2>&1 &

# Wait for startup
sleep 3

# Verify it's running
ps aux | grep uvicorn
curl http://localhost:8080/health
```

### Step 4: Verify Deployment

Check the logs:
```bash
tail -f /tmp/mcp-server.log
```

Test health endpoint:
```bash
curl http://localhost:8080/health
```

You should see:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-14T...",
  "version": "0.1.0",
  "service": "hostaway-mcp"
}
```

### Step 5: Test with Your API Key

Try calling the MCP endpoint with your new API key:
```bash
curl -H "X-API-Key: mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk" \
     http://localhost:8080/mcp
```

---

## Troubleshooting

### Server Won't Start
```bash
# Check logs
tail -100 /tmp/mcp-server.log

# Check if port is in use
lsof -i :8080

# Check Python is available
which python3
python3 --version
```

### Authentication Errors
```bash
# Verify environment variables are set
grep -E "(SUPABASE_URL|SUPABASE_SERVICE_KEY)" .env

# Test Supabase connection
python3 << 'EOF'
from supabase import create_client
import os

# Load .env
from pathlib import Path
env_path = Path('.env')
if env_path.exists():
    for line in env_path.read_text().split('\n'):
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
print(f"URL: {url}")
print(f"Key: {key[:20]}...")

client = create_client(url, key)
result = client.table('api_keys').select('count').execute()
print(f"Connection successful! Found {result.count} API keys")
EOF
```

### Connection Refused from Claude Desktop

1. **Check firewall**: Ensure port 8080 is open on Hostinger
2. **Check server is listening on 0.0.0.0**: `netstat -tlnp | grep 8080`
3. **Test external connection**: From your local machine: `curl http://72.60.233.157:8080/health`

---

## What Changed in This Update

### Database-Backed Authentication
- **Old**: Single static API key from environment variable
- **New**: Multi-tenant API keys stored in Supabase database

### New Features
- API key validation against `api_keys` table
- SHA-256 key hashing for security
- `last_used_at` timestamp tracking
- Organization-level isolation via `request.state`

### Required Environment Variables
```bash
# Added in this deployment:
SUPABASE_URL=https://iixikajovibmfvinkwex.supabase.co
SUPABASE_SERVICE_KEY=<service_role_key>
```

---

## Quick Commands Reference

```bash
# Start server
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080 > /tmp/mcp-server.log 2>&1 &

# Stop server
pkill -f "uvicorn.*main:app"

# View logs
tail -f /tmp/mcp-server.log

# Check status
ps aux | grep uvicorn
curl http://localhost:8080/health

# Restart
pkill -f "uvicorn.*main:app" && sleep 2 && nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080 > /tmp/mcp-server.log 2>&1 &
```
