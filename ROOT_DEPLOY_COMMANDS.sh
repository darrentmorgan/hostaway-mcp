#!/bin/bash
# Root deployment commands for MCP server update
# Run these commands in your browser terminal as root

# Navigate to MCP directory
cd /home/u631126255/hostaway-mcp

# Create backup
echo "Creating backup..."
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz src/ .env 2>/dev/null || true

# Download deployment package from local (you'll need to upload this first)
# Option 1: If you can SCP as root:
# scp darrenmorgan@YOUR_LOCAL_IP:/tmp/hostaway-mcp-deploy.tar.gz .

# Option 2: Upload via File Manager, then extract:
cd /home/u631126255/hostaway-mcp
tar -xzf hostaway-mcp-deploy.tar.gz
rm hostaway-mcp-deploy.tar.gz

# Update .env with Supabase credentials
cat >> .env << 'EOF'

# Supabase Configuration (for API Key validation)
SUPABASE_URL=https://iixikajovibmfvinkwex.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlpeGlrYWpvdmlibWZ2aW5rd2V4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNjg3MDY5NCwiZXhwIjoyMDUyNDQ2Njk0fQ.VCcTWbWE-3Hfi5UaNz4A4yEqqqJdEd3l4sEfhKBBHIg
EOF

# Install supabase dependency
echo "Installing dependencies..."
pip3 install supabase-py

# Stop existing MCP server
echo "Stopping existing MCP server..."
pkill -f "uvicorn.*main:app" || true
pkill -f "python.*mcp" || true
sleep 2

# Start new MCP server
echo "Starting MCP server..."
cd /home/u631126255/hostaway-mcp
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080 > /tmp/mcp-server.log 2>&1 &

# Wait for startup
sleep 5

# Check if process started
if pgrep -f "uvicorn.*main:app" > /dev/null; then
  echo "✓ MCP server started successfully"
  echo "Process ID: $(pgrep -f 'uvicorn.*main:app')"
else
  echo "✗ Failed to start MCP server"
  echo "Checking logs..."
  tail -30 /tmp/mcp-server.log
  exit 1
fi

# Health check
echo ""
echo "Running health check..."
curl -s http://localhost:8080/health | python3 -m json.tool

# Test with API key
echo ""
echo "Testing API key authentication..."
curl -s -H "X-API-Key: mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk" http://localhost:8080/health | python3 -m json.tool

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Logs: tail -f /tmp/mcp-server.log"
echo "Status: ps aux | grep uvicorn"
EOF
