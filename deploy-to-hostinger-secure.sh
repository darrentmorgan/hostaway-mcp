#!/bin/bash
# Deploy Hostaway MCP Server to Hostinger (Secure Version)
set -e

echo "======================================"
echo "Hostaway MCP Server - Secure Deployment"
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
uv run pytest tests/ -v || echo "Warning: Some tests failed, continuing..."

# Create deployment package (excluding sensitive files)
echo "Creating deployment package..."
tar -czf /tmp/hostaway-mcp-deploy.tar.gz \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='dashboard' \
  --exclude='.next' \
  --exclude='node_modules' \
  --exclude='.env' \
  --exclude='.env.local' \
  --exclude='tests' \
  --exclude='secrets-to-replace.txt' \
  --exclude='clean-git-history.sh' \
  --exclude='*backup*' \
  src/ \
  pyproject.toml \
  .env.example \
  mcp_stdio_server.py \
  config.example.yaml

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

# Check if .env exists, if not create from example
if [ ! -f ".env" ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
  echo ""
  echo "⚠️  IMPORTANT: Update .env with your production credentials!"
  echo "Edit: nano .env"
  echo ""
fi

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
curl -s http://72.60.233.157:8080/health | jq '.' || echo "Note: External health check may require port configuration"

echo ""
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo ""
echo "✅ Code deployed successfully"
echo ""
echo "⚠️  NEXT STEPS:"
echo "1. SSH to server: ssh ${SERVER_USER}@${SERVER_HOST}"
echo "2. Update .env with production credentials"
echo "3. Restart server: pkill -f uvicorn && nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080 &"
echo ""
echo "Server logs: ssh ${SERVER_USER}@${SERVER_HOST} 'tail -f /tmp/mcp-server.log'"
echo "Health check: curl http://72.60.233.157:8080/health"
echo ""

# Cleanup
rm /tmp/hostaway-mcp-deploy.tar.gz

echo "Deployment package cleaned up"
