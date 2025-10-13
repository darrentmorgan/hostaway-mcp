#!/bin/bash
# Hostinger VPS Deployment Script for Hostaway MCP Server
# Usage: ./deploy.sh [VPS_HOST]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VPS_HOST=${1:-""}
DEPLOY_DIR="/opt/hostaway-mcp"
LOCAL_DIR=$(pwd)

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_info "Checking deployment requirements..."

    if [ -z "$VPS_HOST" ]; then
        print_error "VPS host not provided. Usage: ./deploy.sh user@your-app.hstgr.cloud"
        exit 1
    fi

    if ! command -v ssh &> /dev/null; then
        print_error "ssh not found. Please install OpenSSH client."
        exit 1
    fi

    if ! command -v rsync &> /dev/null; then
        print_error "rsync not found. Please install rsync."
        exit 1
    fi

    if [ ! -f ".env" ]; then
        print_warning ".env file not found locally. You'll need to create it on the VPS."
    fi

    print_info "✅ Requirements check passed"
}

test_ssh_connection() {
    print_info "Testing SSH connection to $VPS_HOST..."

    if ssh -o ConnectTimeout=10 -q "$VPS_HOST" exit; then
        print_info "✅ SSH connection successful"
    else
        print_error "Cannot connect to $VPS_HOST. Check your SSH credentials."
        exit 1
    fi
}

sync_files() {
    print_info "Syncing files to VPS..."

    rsync -avz --progress \
        --exclude='.git' \
        --exclude='.venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache' \
        --exclude='logs/' \
        --exclude='.env.local' \
        --exclude='node_modules' \
        "$LOCAL_DIR/" "$VPS_HOST:$DEPLOY_DIR/"

    print_info "✅ Files synced successfully"
}

setup_environment() {
    print_info "Setting up environment on VPS..."

    ssh "$VPS_HOST" << 'EOF'
cd /opt/hostaway-mcp

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "\033[1;33m[WARN]\033[0m .env file not found. Creating template..."
    cat > .env << 'ENVEOF'
***REMOVED***
HOSTAWAY_ACCOUNT_ID=your_account_id_here
HOSTAWAY_SECRET_KEY=your_secret_key_here
HOSTAWAY_API_BASE_URL=https://api.hostaway.com/v1

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=production
RATE_LIMIT_IP=15
RATE_LIMIT_ACCOUNT=20
MAX_CONCURRENT_REQUESTS=100
ENVEOF

    chmod 600 .env
    echo -e "\033[1;33m[ACTION REQUIRED]\033[0m Please edit /opt/hostaway-mcp/.env with your actual credentials"
else
    echo -e "\033[0;32m[INFO]\033[0m .env file already exists"
fi

# Secure .env file
chmod 600 .env
EOF

    print_info "✅ Environment setup complete"
}

check_docker() {
    print_info "Checking Docker installation on VPS..."

    ssh "$VPS_HOST" << 'EOF'
if ! command -v docker &> /dev/null; then
    echo -e "\033[1;33m[WARN]\033[0m Docker not found. Installing Docker..."

    # Update system
    apt-get update

    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh

    # Install Docker Compose plugin
    apt-get install -y docker-compose-plugin

    # Clean up
    rm get-docker.sh

    echo -e "\033[0;32m[INFO]\033[0m Docker installed successfully"
else
    echo -e "\033[0;32m[INFO]\033[0m Docker is already installed"
fi

# Verify Docker
docker --version
docker compose version
EOF

    print_info "✅ Docker check complete"
}

deploy_application() {
    print_info "Deploying application on VPS..."

    ssh "$VPS_HOST" << 'EOF'
cd /opt/hostaway-mcp

# Stop existing containers
echo "Stopping existing containers..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

# Build and start new containers
echo "Building and starting containers..."
docker compose -f docker-compose.prod.yml up -d --build

# Wait for health check
echo "Waiting for application to be healthy..."
sleep 10

# Check container status
docker compose -f docker-compose.prod.yml ps

# Show logs
echo "Recent logs:"
docker compose -f docker-compose.prod.yml logs --tail=50
EOF

    print_info "✅ Application deployed successfully"
}

verify_deployment() {
    print_info "Verifying deployment..."

    ssh "$VPS_HOST" << 'EOF'
cd /opt/hostaway-mcp

# Check container health
if docker compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo -e "\033[0;32m[INFO]\033[0m ✅ Container is running"
else
    echo -e "\033[0;31m[ERROR]\033[0m ❌ Container is not running"
    exit 1
fi

# Test health endpoint
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "\033[0;32m[INFO]\033[0m ✅ Health check passed"
else
    echo -e "\033[0;31m[ERROR]\033[0m ❌ Health check failed"
    exit 1
fi

# Test MCP endpoint
if curl -f http://localhost:8080/mcp > /dev/null 2>&1; then
    echo -e "\033[0;32m[INFO]\033[0m ✅ MCP endpoint accessible"
else
    echo -e "\033[0;31m[ERROR]\033[0m ❌ MCP endpoint not accessible"
    exit 1
fi

echo ""
echo "Deployment verification complete!"
echo "MCP URL: http://$(hostname -I | awk '{print $1}'):8080/mcp"
EOF

    print_info "✅ Deployment verified successfully"
}

configure_firewall() {
    print_info "Configuring firewall..."

    ssh "$VPS_HOST" << 'EOF'
# Check if ufw is installed
if command -v ufw &> /dev/null; then
    # Allow port 8080
    ufw allow 8080/tcp

    # Enable firewall if not already enabled
    if ! ufw status | grep -q "Status: active"; then
        echo "y" | ufw enable
    fi

    echo -e "\033[0;32m[INFO]\033[0m Firewall configured to allow port 8080"
else
    echo -e "\033[1;33m[WARN]\033[0m UFW not installed. Firewall not configured."
fi
EOF

    print_info "✅ Firewall configuration complete"
}

# Main deployment flow
main() {
    echo "╔══════════════════════════════════════════════════╗"
    echo "║  Hostaway MCP Server - Hostinger Deployment     ║"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""

    check_requirements
    test_ssh_connection
    sync_files
    setup_environment
    check_docker
    deploy_application
    configure_firewall
    verify_deployment

    echo ""
    echo "╔══════════════════════════════════════════════════╗"
    echo "║           🎉 DEPLOYMENT SUCCESSFUL 🎉            ║"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""
    print_info "Next Steps:"
    echo "  1. Update .env with your Hostaway credentials (if needed):"
    echo "     ssh $VPS_HOST 'nano /opt/hostaway-mcp/.env'"
    echo ""
    echo "  2. Restart the application after updating credentials:"
    echo "     ssh $VPS_HOST 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml restart'"
    echo ""
    echo "  3. Configure MCP client with URL:"
    echo "     ssh $VPS_HOST 'curl -s ifconfig.me | xargs -I {} echo \"http://{}:8080/mcp\"'"
    echo ""
    echo "  4. Monitor logs:"
    echo "     ssh $VPS_HOST 'cd /opt/hostaway-mcp && docker compose -f docker-compose.prod.yml logs -f'"
    echo ""
}

# Run main function
main
