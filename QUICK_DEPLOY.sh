#!/bin/bash
# Quick deployment (skips tests for hotfix)

echo "Step 1: Uploading package to Hostinger..."
scp /tmp/hostaway-mcp-deploy.tar.gz u631126255@72.60.233.157:/home/u631126255/hostaway-mcp/

echo ""
echo "Step 2: Run these commands on the server:"
echo ""
echo "ssh u631126255@72.60.233.157"
echo ""
echo "Then copy-paste this entire block:"
echo ""
cat << 'ENDSSH'
cd /home/u631126255/hostaway-mcp

# Backup current version
echo "Creating backup..."
if [ -d "src" ]; then
  tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz src/ .env 2>/dev/null || true
fi

# Extract new version
echo "Extracting new version..."
tar -xzf hostaway-mcp-deploy.tar.gz
rm hostaway-mcp-deploy.tar.gz

# Update .env with Supabase credentials (append if not exists)
if ! grep -q "SUPABASE_URL" .env 2>/dev/null; then
  echo "" >> .env
  echo "# Supabase Configuration (for API Key validation)" >> .env
  echo "SUPABASE_URL=https://iixikajovibmfvinkwex.supabase.co" >> .env
  echo "SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlpeGlrYWpvdmlibWZ2aW5rd2V4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNjg3MDY5NCwiZXhwIjoyMDUyNDQ2Njk0fQ.VCcTWbWE-3Hfi5UaNz4A4yEqqqJdEd3l4sEfhKBBHIg" >> .env
  echo "Supabase credentials added to .env"
else
  echo "Supabase credentials already exist in .env"
fi

# Install/update dependencies
echo "Installing dependencies..."
pip3 install --user supabase-py || pip3 install supabase

# Stop existing MCP server
echo "Stopping existing MCP server..."
pkill -f "uvicorn.*main:app" || true
pkill -f "python.*mcp" || true
sleep 2

# Start new MCP server
echo "Starting MCP server..."
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
  tail -20 /tmp/mcp-server.log
  exit 1
fi

# Health check
echo ""
echo "Running health check..."
sleep 2
curl -s http://localhost:8080/health | python3 -m json.tool || echo "Warning: Health check failed"

echo ""
echo "Testing API key authentication..."
curl -s -H "X-API-Key: mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk" http://localhost:8080/health | python3 -m json.tool || echo "Note: Check logs for details"

echo ""
echo "Deployment complete!"
echo "Check logs: tail -f /tmp/mcp-server.log"
ENDSSH
