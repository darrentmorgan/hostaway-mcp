#!/bin/bash
# Deploy Hostaway MCP Server to Hostinger
set -e

echo "======================================"
echo "Hostaway MCP Server - Deployment Script"
echo "======================================"

# Configuration
SERVER_USER="u631126255"
SERVER_HOST="72.60.233.157"
SERVER_PATH="/home/u631126255/hostaway-mcp"
LOCAL_PATH="/Users/darrenmorgan/AI_Projects/hostaway-mcp"

echo ""
echo "Step 1: Building project locally..."
cd "$LOCAL_PATH"

# Run tests
echo "Running tests..."
uv run pytest tests/ -v

# Create deployment package
echo "Creating deployment package..."
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
  .env \
  mcp_stdio_server.py

echo ""
echo "Step 2: Uploading to Hostinger..."
scp /tmp/hostaway-mcp-deploy.tar.gz ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/

echo ""
echo "Step 3: Deploying on server..."
ssh ${SERVER_USER}@${SERVER_HOST} << 'ENDSSH'
cd /home/u631126255/hostaway-mcp

# Backup current version
echo "Creating backup..."
if [ -d "src" ]; then
  tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz src/ .env || true
fi

# Extract new version
echo "Extracting new version..."
tar -xzf hostaway-mcp-deploy.tar.gz
rm hostaway-mcp-deploy.tar.gz

# Update environment variables (keep existing, add new ones)
echo "Updating environment variables..."
cat >> .env << 'EOF'

# Supabase Configuration (for API Key validation)
SUPABASE_URL=https://iixikajovibmfvinkwex.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlpeGlrYWpvdmlibWZ2aW5rd2V4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNjg3MDY5NCwiZXhwIjoyMDUyNDQ2Njk0fQ.VCcTWbWE-3Hfi5UaNz4A4yEqqqJdEd3l4sEfhKBBHIg
EOF

# Restart the service
echo "Restarting MCP server..."
# Kill existing process
pkill -f "python.*mcp_stdio_server.py" || true
pkill -f "uvicorn.*main:app" || true

# Start new process in background
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080 > /tmp/mcp-server.log 2>&1 &

# Wait a moment for startup
sleep 3

# Check if process started
if pgrep -f "uvicorn.*main:app" > /dev/null; then
  echo "✓ MCP server started successfully"
  echo "Process ID: $(pgrep -f 'uvicorn.*main:app')"
else
  echo "✗ Failed to start MCP server"
  echo "Check logs: tail -f /tmp/mcp-server.log"
  exit 1
fi

# Health check
echo "Running health check..."
sleep 2
curl -s http://localhost:8080/health || echo "Warning: Health check failed"

ENDSSH

echo ""
echo "Step 4: Verifying deployment..."
curl -s https://72.60.233.157:8080/health | jq '.' || echo "Note: External health check requires port forwarding"

echo ""
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo ""
echo "Server logs: ssh ${SERVER_USER}@${SERVER_HOST} 'tail -f /tmp/mcp-server.log'"
echo "Health check: curl http://72.60.233.157:8080/health"
echo ""

# Cleanup
rm /tmp/hostaway-mcp-deploy.tar.gz

echo "Deployment package cleaned up"
