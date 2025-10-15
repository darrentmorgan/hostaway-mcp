#!/bin/bash

# Security Remediation Script for Hostaway MCP
# This script helps remediate security issues found in the audit

set -e

echo "========================================="
echo "Security Remediation Script"
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "This script must be run from within the git repository"
    exit 1
fi

echo "Step 1: Checking for exposed .env file"
echo "----------------------------------------"
if [ -f ".env" ]; then
    if git ls-files --error-unmatch .env 2>/dev/null; then
        print_warning ".env file is tracked by git!"
        echo "Removing .env from git tracking..."
        git rm --cached .env
        print_status ".env removed from git tracking"
    else
        print_status ".env file exists but is not tracked by git"
    fi
else
    print_status "No .env file found in repository"
fi

echo ""
echo "Step 2: Ensuring .gitignore is properly configured"
echo "---------------------------------------------------"
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    print_warning ".env not found in .gitignore"
    echo ".env" >> .gitignore
    print_status "Added .env to .gitignore"
else
    print_status ".env is already in .gitignore"
fi

# Check for other sensitive patterns
for pattern in "*.pem" "*.key" "*.crt" "*.p12" "*_rsa" "*_dsa" "*_ecdsa" "*_ed25519"; do
    if ! grep -q "$pattern" .gitignore 2>/dev/null; then
        echo "$pattern" >> .gitignore
        print_status "Added $pattern to .gitignore"
    fi
done

echo ""
echo "Step 3: Creating secure .env.example template"
echo "----------------------------------------------"
cat > .env.example.secure << 'EOF'
# Hostaway MCP Environment Configuration
# SECURITY WARNING: Never commit actual credentials to version control!
# Copy this file to .env and fill in your actual values

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=<your-anon-key-here>
SUPABASE_SERVICE_KEY=<your-service-role-key-here>

# MCP API Configuration
MCP_API_KEY=<your-mcp-api-key-here>
MCP_API_URL=http://localhost:8000

# Hostaway API Configuration
HOSTAWAY_API_KEY=<your-hostaway-api-key-here>
HOSTAWAY_CLIENT_ID=<your-client-id-here>
HOSTAWAY_SECRET_KEY=<your-secret-key-here>

# Security Settings
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=60
ENABLE_API_KEY_VALIDATION=true
ENABLE_CORS=true
ALLOWED_ORIGINS=https://your-domain.com

# Logging Configuration
LOG_LEVEL=info
ENABLE_AUDIT_LOGGING=true

# Environment
ENVIRONMENT=development  # development | staging | production
EOF

print_status "Created secure .env.example template"

echo ""
echo "Step 4: Searching for hardcoded secrets in scripts"
echo "---------------------------------------------------"
FILES_WITH_SECRETS=$(grep -l "eyJhbGciOiJIUzI1NiIs\|mcp_[A-Za-z0-9]\{20,\}" *.sh *.md 2>/dev/null || true)

if [ -n "$FILES_WITH_SECRETS" ]; then
    print_warning "Found potential secrets in the following files:"
    echo "$FILES_WITH_SECRETS" | while read file; do
        echo "  - $file"
    done
    echo ""
    echo "Creating cleaned versions of deployment scripts..."

    # Create cleaned deployment script template
    cat > deploy-clean.sh << 'EOF'
#!/bin/bash
# Secure Deployment Script Template

set -e

# Load environment variables from secure location
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found"
    echo "Please create .env from .env.example"
    exit 1
fi

# Verify required environment variables
required_vars=(
    "SUPABASE_URL"
    "SUPABASE_SERVICE_KEY"
    "MCP_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

echo "Environment variables loaded successfully"
# Add your deployment commands here
EOF
    chmod +x deploy-clean.sh
    print_status "Created clean deployment script template (deploy-clean.sh)"
else
    print_status "No hardcoded secrets found in shell scripts"
fi

echo ""
echo "Step 5: Setting up pre-commit hooks"
echo "------------------------------------"
if [ ! -f ".pre-commit-config.yaml" ]; then
    print_warning "No pre-commit configuration found"
else
    print_status "Pre-commit configuration exists"

    # Check if gitleaks hook is configured
    if ! grep -q "gitleaks" .pre-commit-config.yaml 2>/dev/null; then
        print_warning "Gitleaks not configured in pre-commit"
        echo "Consider adding gitleaks to your pre-commit configuration"
    else
        print_status "Gitleaks is configured in pre-commit"
    fi
fi

echo ""
echo "Step 6: Creating secret scanning script"
echo "----------------------------------------"
cat > scan-secrets.sh << 'EOF'
#!/bin/bash
# Quick secret scanning script

echo "Running secret scan..."

# Check for common secret patterns
patterns=(
    "password.*=.*['\"].*['\"]"
    "api[_-]?key.*=.*['\"].*['\"]"
    "secret.*=.*['\"].*['\"]"
    "token.*=.*['\"].*['\"]"
    "Bearer [A-Za-z0-9+/=]{20,}"
    "Basic [A-Za-z0-9+/=]{20,}"
)

found_issues=0
for pattern in "${patterns[@]}"; do
    results=$(grep -r -i "$pattern" --include="*.py" --include="*.ts" --include="*.js" --include="*.sh" --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir=".venv" . 2>/dev/null || true)
    if [ -n "$results" ]; then
        echo "Found potential secrets matching pattern: $pattern"
        echo "$results"
        found_issues=1
    fi
done

if [ $found_issues -eq 0 ]; then
    echo "No obvious secrets found in code files"
else
    echo "WARNING: Potential secrets found. Please review and remove them."
fi
EOF

chmod +x scan-secrets.sh
print_status "Created secret scanning script (scan-secrets.sh)"

echo ""
echo "========================================="
echo "Security Remediation Summary"
echo "========================================="
echo ""
print_status "Completed initial security remediation steps"
echo ""
echo "CRITICAL ACTIONS REQUIRED:"
echo "1. ${RED}IMMEDIATELY${NC} rotate all Supabase keys in your Supabase dashboard"
echo "2. ${RED}IMMEDIATELY${NC} regenerate all MCP API keys"
echo "3. ${RED}IMMEDIATELY${NC} update production deployments with new credentials"
echo ""
echo "Next steps:"
echo "1. Review and update files with hardcoded secrets"
echo "2. Run: ./scan-secrets.sh to check for remaining secrets"
echo "3. Configure secret management (e.g., HashiCorp Vault, AWS Secrets Manager)"
echo "4. Set up CI/CD secret scanning with gitleaks"
echo "5. Train team on secure coding practices"
echo ""
echo "To permanently remove secrets from git history, consider using:"
echo "  - BFG Repo-Cleaner: https://rtyley.github.io/bfg-repo-cleaner/"
echo "  - git filter-branch (more complex but built-in)"
echo ""
print_warning "Remember: Once secrets are exposed in git history, they should be considered compromised!"