#!/bin/bash
# Cloudflare Tunnel Setup with Manual DNS (Keep Hostinger Nameservers)
# Run this script on your Hostinger VPS (72.60.233.157)

set -e

DOMAIN="mcp.baliluxurystays.com"
SERVICE_PORT="8080"

echo "🚀 Cloudflare Tunnel Setup (Manual DNS)"
echo "========================================"
echo "Domain: $DOMAIN"
echo "Service: http://localhost:$SERVICE_PORT"
echo ""
echo "NOTE: This setup keeps your Hostinger nameservers."
echo "You'll add ONE CNAME record manually at the end."
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

# Step 2: Authenticate with Cloudflare (only need Cloudflare account, not domain on Cloudflare)
echo "🔐 Step 2: Authenticate with Cloudflare"
echo "----------------------------------------"
echo "This will open a browser window for authentication."
echo "You only need a FREE Cloudflare account (no domain required)."
echo ""
read -p "Press Enter to continue..."
cloudflared tunnel login
echo "✓ Authentication complete"
echo ""

# Step 3: Create tunnel
echo "🔧 Step 3: Creating tunnel..."
echo "----------------------------------------"
TUNNEL_NAME="hostaway-mcp"

# Check if tunnel already exists
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo "⚠️  Tunnel '$TUNNEL_NAME' already exists, using existing tunnel"
    TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
else
    cloudflared tunnel create $TUNNEL_NAME
    TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
    echo "✓ Tunnel created: $TUNNEL_NAME"
fi

echo "Tunnel ID: $TUNNEL_ID"
echo ""

# Get the tunnel hostname
TUNNEL_HOSTNAME="${TUNNEL_ID}.cfargotunnel.com"
echo "📝 Tunnel Hostname: $TUNNEL_HOSTNAME"
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

# Step 5: Install as a service
echo "⚙️  Step 5: Installing tunnel as a system service..."
echo "----------------------------------------"
sudo cloudflared service install
echo "✓ Service installed"
echo ""

# Step 6: Start the service
echo "🚀 Step 6: Starting tunnel service..."
echo "----------------------------------------"
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
sleep 3
echo "✓ Tunnel service started and enabled"
echo ""

# Step 7: Check status
echo "✅ Step 7: Checking tunnel status..."
echo "----------------------------------------"
sudo systemctl status cloudflared --no-pager || true
echo ""

# Final instructions
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Cloudflare Tunnel is Running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  IMPORTANT: Add This DNS Record at Hostinger"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Go to Hostinger DNS Management for baliluxurystays.com:"
echo ""
echo "  Type:   CNAME"
echo "  Name:   mcp"
echo "  Target: $TUNNEL_HOSTNAME"
echo "  TTL:    300 (or 5 minutes)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "After adding the CNAME record, wait 1-5 minutes for DNS propagation."
echo ""
echo "Then test:"
echo "  curl https://$DOMAIN/health"
echo ""
echo "Expected response:"
echo '  {"status": "healthy"}'
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
