#!/bin/bash
# Cloudflare Tunnel Setup for mcp.baliluxurystays.com
# Run this script on your Hostinger VPS (72.60.233.157)

set -e

DOMAIN="mcp.baliluxurystays.com"
SERVICE_PORT="8080"

echo "🚀 Cloudflare Tunnel Setup"
echo "=========================="
echo "Domain: $DOMAIN"
echo "Service: http://localhost:$SERVICE_PORT"
echo ""

# Step 1: Install cloudflared
echo "📦 Step 1: Installing cloudflared..."
echo "----------------------------------------"
if command -v cloudflared &> /dev/null; then
    echo "✓ cloudflared already installed"
    cloudflared --version
else
    echo "Downloading cloudflared..."
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
    sudo mv cloudflared /usr/local/bin/
    sudo chmod +x /usr/local/bin/cloudflared
    echo "✓ cloudflared installed"
    cloudflared --version
fi
echo ""

# Step 2: Authenticate with Cloudflare
echo "🔐 Step 2: Authenticate with Cloudflare"
echo "----------------------------------------"
echo "This will open a browser window for authentication."
echo "Follow the prompts to authorize cloudflared."
echo ""
read -p "Press Enter to continue..."
cloudflared tunnel login
echo "✓ Authentication complete"
echo ""

# Step 3: Create tunnel
echo "🔧 Step 3: Creating tunnel..."
echo "----------------------------------------"
TUNNEL_NAME="hostaway-mcp"
cloudflared tunnel create $TUNNEL_NAME
echo "✓ Tunnel created: $TUNNEL_NAME"
echo ""

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
echo "Tunnel ID: $TUNNEL_ID"
echo ""

# Step 4: Configure tunnel
echo "📝 Step 4: Creating tunnel configuration..."
echo "----------------------------------------"
sudo mkdir -p /etc/cloudflared
sudo tee /etc/cloudflared/config.yml > /dev/null <<EOF
tunnel: $TUNNEL_ID
credentials-file: /root/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: $DOMAIN
    service: http://localhost:$SERVICE_PORT
  - service: http_status:404
EOF
echo "✓ Configuration created at /etc/cloudflared/config.yml"
echo ""

# Step 5: Route DNS
echo "🌐 Step 5: Routing DNS..."
echo "----------------------------------------"
cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN
echo "✓ DNS route created for $DOMAIN"
echo ""

# Step 6: Install as a service
echo "⚙️  Step 6: Installing tunnel as a system service..."
echo "----------------------------------------"
sudo cloudflared service install
echo "✓ Service installed"
echo ""

# Step 7: Start the service
echo "🚀 Step 7: Starting tunnel service..."
echo "----------------------------------------"
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
echo "✓ Tunnel service started and enabled"
echo ""

# Step 8: Check status
echo "✅ Step 8: Checking tunnel status..."
echo "----------------------------------------"
sudo systemctl status cloudflared --no-pager
echo ""

# Final verification
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Your MCP server is now available at:"
echo "  🔗 https://$DOMAIN"
echo ""
echo "Test the connection:"
echo "  curl https://$DOMAIN/health"
echo ""
echo "Claude MCP Connector Configuration:"
echo "  Name: Hostaway MCP"
echo "  URL: https://$DOMAIN"
echo "  OAuth Client ID: (empty)"
echo "  OAuth Client Secret: (empty)"
echo ""
echo "To check tunnel status:"
echo "  sudo systemctl status cloudflared"
echo ""
echo "To view tunnel logs:"
echo "  sudo journalctl -u cloudflared -f"
echo ""
echo "To restart tunnel:"
echo "  sudo systemctl restart cloudflared"
echo ""
