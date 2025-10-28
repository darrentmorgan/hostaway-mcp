#!/bin/bash
# Setup HTTPS with Nginx and Let's Encrypt

set -e

echo "🔒 Setting up HTTPS with Nginx + Let's Encrypt"
echo "==============================================="
echo ""

# Check if domain is provided
if [ -z "$1" ]; then
    echo "❌ Error: Domain name required"
    echo ""
    echo "Usage: ./setup-https-nginx.sh yourdomain.com your@email.com"
    echo ""
    exit 1
fi

if [ -z "$2" ]; then
    echo "❌ Error: Email required for Let's Encrypt"
    echo ""
    echo "Usage: ./setup-https-nginx.sh yourdomain.com your@email.com"
    echo ""
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Update nginx.conf with domain
echo "📝 Updating nginx.conf with your domain..."
sed -i "s/YOUR_DOMAIN/$DOMAIN/g" nginx.conf
sed -i "s/server_name _;/server_name $DOMAIN;/g" nginx.conf

# Create directories for certbot
echo "📁 Creating directories..."
mkdir -p certbot/conf
mkdir -p certbot/www

# Generate initial certificate
echo "🔐 Generating SSL certificate..."
echo ""
echo "Run this command on your Hostinger VPS:"
echo ""
echo "docker compose -f docker-compose.prod.yml run --rm certbot certonly --webroot --webroot-path /var/www/certbot --email $EMAIL --agree-tos --no-eff-email -d $DOMAIN"
echo ""

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update your DNS to point $DOMAIN to 72.60.233.157"
echo "2. Run: docker compose -f docker-compose.prod.yml up -d"
echo "3. Generate certificate (command above)"
echo "4. Restart nginx: docker compose -f docker-compose.prod.yml restart nginx"
echo ""
echo "Your MCP server will be available at: https://$DOMAIN"
