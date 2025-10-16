#!/bin/bash
# Automated deployment to production server
set -e

echo "========================================"
echo "Hostaway MCP - Automated Deployment"
echo "========================================"

# Configuration
SERVER="root@72.60.233.157"
REMOTE_PATH="/opt/hostaway-mcp"
LOCAL_PATH="/Users/darrenmorgan/AI_Projects/hostaway-mcp"

echo ""
echo "Step 1: Creating deployment package..."
cd "$LOCAL_PATH"

tar -czf /tmp/hostaway-mcp-deploy.tar.gz \
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

echo "✓ Package created: /tmp/hostaway-mcp-deploy.tar.gz"

echo ""
echo "Step 2: Uploading to server..."
scp /tmp/hostaway-mcp-deploy.tar.gz ${SERVER}:${REMOTE_PATH}/

echo "✓ Upload complete"

echo ""
echo "Step 3: Deploying on server..."
ssh ${SERVER} bash << 'ENDSSH'
set -e

cd /opt/hostaway-mcp

# Backup
echo "Creating backup..."
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz src/ .env 2>/dev/null || true

# Extract
echo "Extracting new version..."
tar -xzf hostaway-mcp-deploy.tar.gz
rm hostaway-mcp-deploy.tar.gz

# Check if Supabase config already exists
if ! grep -q "SUPABASE_URL" .env 2>/dev/null; then
  echo "Adding Supabase configuration..."
  cat >> .env << 'EOF'

# Supabase Configuration (for API Key validation)
SUPABASE_URL=https://iixikajovibmfvinkwex.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlpeGlrYWpvdmlibWZ2aW5rd2V4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNjg3MDY5NCwiZXhwIjoyMDUyNDQ2Njk0fQ.VCcTWbWE-3Hfi5UaNz4A4yEqqqJdEd3l4sEfhKBBHIg
EOF
else
  echo "Supabase config already exists"
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install supabase-py 2>/dev/null || pip3 install --user supabase-py

# Restart server
echo "Restarting MCP server..."
pkill -f "uvicorn.*main:app" 2>/dev/null || true
sleep 2

cd /opt/hostaway-mcp
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080 > /tmp/mcp-server.log 2>&1 &

# Wait for startup
sleep 5

# Check if started
if pgrep -f "uvicorn.*main:app" > /dev/null; then
  echo "✓ MCP server started successfully"
  PID=$(pgrep -f "uvicorn.*main:app")
  echo "  Process ID: $PID"
else
  echo "✗ Failed to start MCP server"
  echo "Logs:"
  tail -30 /tmp/mcp-server.log
  exit 1
fi

# Health check
echo ""
echo "Running health check..."
sleep 2
if curl -s http://localhost:8080/health > /dev/null; then
  echo "✓ Health check passed"
  curl -s http://localhost:8080/health | python3 -m json.tool
else
  echo "✗ Health check failed"
  exit 1
fi

# Test API key
echo ""
echo "Testing API key authentication..."
if curl -s -H "X-API-Key: mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk" http://localhost:8080/health > /dev/null; then
  echo "✓ API key authentication working"
else
  echo "⚠ API key test failed (check logs)"
  tail -20 /tmp/mcp-server.log
fi

ENDSSH

echo ""
echo "========================================"
echo "✓ Deployment Complete!"
echo "========================================"
echo ""
echo "Server status:"
echo "  URL: http://72.60.233.157:8080"
echo "  Logs: ssh ${SERVER} 'tail -f /tmp/mcp-server.log'"
echo ""
echo "Next steps:"
echo "  1. Restart Claude Desktop"
echo "  2. Test the MCP connection"
echo ""

# Cleanup
rm /tmp/hostaway-mcp-deploy.tar.gz
echo "✓ Cleaned up local deployment package"
