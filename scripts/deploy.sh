#!/bin/bash
# Deployment script for Hostaway MCP Server to Hostinger VPS
# Usage: ./scripts/deploy.sh [staging|production]

set -e  # Exit on error

# Configuration
SERVER_IP="${DEPLOY_SERVER_IP:-72.60.233.157}"
SERVER_USER="${DEPLOY_USER:-root}"
SERVER_PORT="${DEPLOY_PORT:-22}"
DEPLOY_PATH="${DEPLOY_PATH:-/var/www/hostaway-mcp}"
SERVICE_NAME="${SERVICE_NAME:-hostaway-mcp}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if SSH key is configured
check_ssh() {
    log_info "Checking SSH connection to ${SERVER_USER}@${SERVER_IP}..."
    if ssh -o ConnectTimeout=5 -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} "echo 'SSH connection successful'" > /dev/null 2>&1; then
        log_info "SSH connection verified ✓"
        return 0
    else
        log_error "Cannot connect to server. Please check SSH configuration."
        log_info "Run: ssh-copy-id -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP}"
        exit 1
    fi
}

# Build the application
build_app() {
    log_info "Building application..."

    # Run tests if they exist
    if [ -f "pyproject.toml" ] && grep -q "pytest" pyproject.toml; then
        log_info "Running tests..."
        uv run pytest tests/ -v || {
            log_error "Tests failed. Aborting deployment."
            exit 1
        }
    fi

    log_info "Build completed ✓"
}

# Deploy to server
deploy() {
    local ENVIRONMENT=${1:-production}

    log_info "Deploying to ${ENVIRONMENT}..."

    # Create deployment directory on server if it doesn't exist
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} "mkdir -p ${DEPLOY_PATH}"

    # Sync files (excluding local dev files)
    log_info "Syncing files to server..."
    rsync -avz --delete \
        --exclude '.git' \
        --exclude '.env' \
        --exclude '.env.local' \
        --exclude '__pycache__' \
        --exclude '.venv' \
        --exclude 'venv' \
        --exclude 'node_modules' \
        --exclude '.next' \
        --exclude 'dashboard/.next' \
        --exclude '.pytest_cache' \
        --exclude '.mypy_cache' \
        --exclude '.ruff_cache' \
        --exclude 'coverage' \
        --exclude '*.pyc' \
        --exclude '.DS_Store' \
        --exclude 'supabase/.temp' \
        -e "ssh -p ${SERVER_PORT}" \
        ./ ${SERVER_USER}@${SERVER_IP}:${DEPLOY_PATH}/

    # Install dependencies and restart service on server
    log_info "Installing dependencies and restarting service..."
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} << ENDSSH
        cd ${DEPLOY_PATH}

        # Install Python dependencies
        if command -v uv &> /dev/null; then
            uv sync --no-dev
        else
            pip install -e .
        fi

        # Restart systemd service if it exists
        if systemctl is-active --quiet ${SERVICE_NAME}; then
            sudo systemctl restart ${SERVICE_NAME}
            echo "Service ${SERVICE_NAME} restarted"
        else
            echo "Note: No systemd service found. You may need to restart manually."
        fi

        # Check service status
        if systemctl is-active --quiet ${SERVICE_NAME}; then
            echo "✓ Service is running"
            systemctl status ${SERVICE_NAME} --no-pager -l
        fi
ENDSSH

    log_info "Deployment completed successfully ✓"
    log_info "Server: http://${SERVER_IP}:8080"
}

# Main deployment flow
main() {
    local ENVIRONMENT=${1:-production}

    log_info "Starting deployment to ${ENVIRONMENT}..."
    log_info "Server: ${SERVER_USER}@${SERVER_IP}:${SERVER_PORT}"
    log_info "Path: ${DEPLOY_PATH}"

    check_ssh
    build_app
    deploy ${ENVIRONMENT}

    log_info "Deployment complete! 🚀"
}

# Run main function
main "$@"
