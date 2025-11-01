#!/bin/bash
# Temporary SSH Tunnel to access MCP server while DNS propagates
# This creates a local tunnel to the remote MCP server

echo "🔧 Starting SSH tunnel to Hostaway MCP server..."
echo "This will tunnel localhost:8000 → remote server:8080"
echo ""
echo "Keep this terminal window open while using Claude."
echo "Press Ctrl+C to stop the tunnel."
echo ""

ssh -i ~/.ssh/hostaway-deploy \
    -L 8000:localhost:8080 \
    -N \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    root@72.60.233.157
