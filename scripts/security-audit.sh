#!/bin/bash
# Security Audit Script for Hostaway MCP
# Runs comprehensive security checks across the codebase

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Hostaway MCP Security Audit${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Track if any issues were found
ISSUES_FOUND=0

# Function to run a security check
run_check() {
    local name="$1"
    local command="$2"

    echo -e "${YELLOW}Running: ${name}${NC}"
    if eval "$command"; then
        echo -e "${GREEN}✓ ${name} passed${NC}"
    else
        echo -e "${RED}✗ ${name} found issues${NC}"
        ISSUES_FOUND=1
    fi
    echo ""
}

# 1. Check for secrets with gitleaks
echo -e "${BLUE}1. Secret Detection (Gitleaks)${NC}"
if command -v gitleaks &> /dev/null; then
    run_check "Gitleaks scan" "gitleaks detect --config .gitleaks.toml --verbose --no-git"
else
    echo -e "${RED}Gitleaks not installed. Install with: brew install gitleaks${NC}"
    ISSUES_FOUND=1
fi

# 2. Python security audit with bandit
echo -e "${BLUE}2. Python Security Audit (Bandit)${NC}"
if command -v bandit &> /dev/null; then
    run_check "Bandit security scan" "bandit -ll -r src/ --skip B113 -f json -o /tmp/bandit-report.json 2>/dev/null && echo 'No high/medium severity issues found'"
else
    echo -e "${RED}Bandit not installed. Install with: pip install bandit${NC}"
    ISSUES_FOUND=1
fi

# 3. Check Python dependencies for vulnerabilities
echo -e "${BLUE}3. Python Dependency Vulnerabilities (Safety)${NC}"
if command -v safety &> /dev/null; then
    if [ -f "requirements.txt" ]; then
        run_check "Safety dependency check" "safety check --json --continue-on-error"
    else
        echo -e "${YELLOW}No requirements.txt found${NC}"
    fi
else
    echo -e "${YELLOW}Safety not installed. Install with: pip install safety${NC}"
fi

# 4. Check for hardcoded credentials
echo -e "${BLUE}4. Hardcoded Credentials Check${NC}"
CRED_PATTERN='(password|passwd|pwd|secret|api[_-]?key|token|credential)[[:space:]]*[=:][[:space:]]*[\"'\'''][^\"'\'']{8,}[\"'\'']'
echo "Scanning for hardcoded credentials..."
CRED_RESULTS=$(grep -r -E "$CRED_PATTERN" \
    --include="*.py" \
    --include="*.js" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.env*" \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=dist \
    --exclude-dir=.next \
    --exclude-dir=venv \
    --exclude-dir=.venv \
    --exclude="*.test.*" \
    --exclude="*.spec.*" \
    . 2>/dev/null | \
    grep -v "example\|placeholder\|your[_-]api\|test[_-]api\|mock\|fake" || true)

if [ -z "$CRED_RESULTS" ]; then
    echo -e "${GREEN}✓ No hardcoded credentials found${NC}"
else
    echo -e "${RED}✗ Potential hardcoded credentials found:${NC}"
    echo "$CRED_RESULTS"
    ISSUES_FOUND=1
fi
echo ""

# 5. Check for environment files that shouldn't be committed
echo -e "${BLUE}5. Environment File Check${NC}"
ENV_FILES=".env .env.local .env.production .env.development"
ENV_ISSUES=0
for file in $ENV_FILES; do
    if [ -f "$file" ]; then
        if git ls-files --error-unmatch "$file" 2>/dev/null; then
            echo -e "${RED}✗ $file is tracked by git!${NC}"
            ENV_ISSUES=1
            ISSUES_FOUND=1
        else
            echo -e "${GREEN}✓ $file exists but is not tracked${NC}"
        fi
    fi
done
if [ $ENV_ISSUES -eq 0 ] && [ -f .gitignore ]; then
    echo -e "${GREEN}✓ Environment files properly configured${NC}"
fi
echo ""

# 6. Check SSL/TLS configuration
echo -e "${BLUE}6. SSL/TLS Configuration Check${NC}"
echo "Checking for insecure SSL/TLS usage..."
SSL_ISSUES=$(grep -r "verify=False\|ssl_verify=False\|SSL_VERIFY=False\|sslmode=disable" \
    --include="*.py" \
    --include="*.js" \
    --include="*.ts" \
    --exclude-dir=node_modules \
    --exclude-dir=tests \
    --exclude-dir=.git \
    . 2>/dev/null || true)

if [ -z "$SSL_ISSUES" ]; then
    echo -e "${GREEN}✓ No insecure SSL/TLS configuration found${NC}"
else
    echo -e "${RED}✗ Insecure SSL/TLS configuration found:${NC}"
    echo "$SSL_ISSUES"
    ISSUES_FOUND=1
fi
echo ""

# 7. Check for SQL injection vulnerabilities (basic)
echo -e "${BLUE}7. SQL Injection Pattern Check${NC}"
echo "Scanning for potential SQL injection patterns..."
SQL_PATTERNS='(f-string|format|%)\s*.*\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)'
SQL_ISSUES=$(grep -r -E "$SQL_PATTERNS" \
    --include="*.py" \
    --exclude-dir=tests \
    --exclude-dir=.git \
    --exclude-dir=venv \
    . 2>/dev/null || true)

if [ -z "$SQL_ISSUES" ]; then
    echo -e "${GREEN}✓ No obvious SQL injection patterns found${NC}"
else
    echo -e "${YELLOW}⚠ Potential SQL injection patterns found (review manually):${NC}"
    echo "$SQL_ISSUES" | head -10
    echo -e "${YELLOW}Use parameterized queries instead${NC}"
fi
echo ""

# 8. Check security headers in Next.js config
echo -e "${BLUE}8. Next.js Security Headers Check${NC}"
if [ -f "dashboard/next.config.js" ] || [ -f "dashboard/next.config.mjs" ]; then
    HEADERS_CHECK=$(grep -l "headers\|securityHeaders" dashboard/next.config.* 2>/dev/null || true)
    if [ -n "$HEADERS_CHECK" ]; then
        echo -e "${GREEN}✓ Security headers configuration found${NC}"
    else
        echo -e "${YELLOW}⚠ No security headers configuration found in Next.js${NC}"
        ISSUES_FOUND=1
    fi
else
    echo -e "${YELLOW}No Next.js config file found${NC}"
fi
echo ""

# 9. Check for outdated dependencies
echo -e "${BLUE}9. Outdated Dependencies Check${NC}"
if [ -f "requirements.txt" ]; then
    echo "Python dependencies:"
    pip list --outdated 2>/dev/null | head -10 || echo "Unable to check Python dependencies"
fi

if [ -f "dashboard/package.json" ]; then
    echo "JavaScript dependencies:"
    cd dashboard && npm outdated 2>/dev/null | head -10 || echo "Unable to check npm dependencies"
    cd ..
fi
echo ""

# 10. Check file permissions
echo -e "${BLUE}10. File Permissions Check${NC}"
echo "Checking for overly permissive files..."
PERM_ISSUES=$(find . -type f \( -perm -o+w -o -perm -g+w \) \
    -not -path "./.git/*" \
    -not -path "./node_modules/*" \
    -not -path "./.next/*" \
    2>/dev/null | head -10 || true)

if [ -z "$PERM_ISSUES" ]; then
    echo -e "${GREEN}✓ No overly permissive files found${NC}"
else
    echo -e "${YELLOW}⚠ Files with write permissions for group/others:${NC}"
    echo "$PERM_ISSUES"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Security Audit Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ All security checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Security issues detected. Please review and fix.${NC}"
    echo ""
    echo "Recommendations:"
    echo "1. Run 'pre-commit install' to enable automatic security checks"
    echo "2. Fix any hardcoded credentials or secrets"
    echo "3. Update outdated dependencies with security patches"
    echo "4. Configure proper security headers in Next.js"
    echo "5. Use parameterized queries for all database operations"
    echo "6. Enable SSL verification for all external connections"
    echo ""
    echo "For detailed reports, check:"
    echo "  - Bandit: /tmp/bandit-report.json"
    echo "  - Run 'gitleaks detect --report-path gitleaks-report.json' for detailed secret scan"
    exit 1
fi
