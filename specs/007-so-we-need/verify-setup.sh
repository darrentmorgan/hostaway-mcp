#!/bin/bash
#
# CI/CD Setup Verification Script
# Verifies that Phase 2 (Foundational) manual steps are complete
#
# Usage: ./verify-setup.sh

set -e

echo "🔍 Verifying CI/CD Setup (Phase 2: Foundational)"
echo "=================================================="
echo ""

ERRORS=0
WARNINGS=0

# Check 1: SSH key pair exists
echo "✓ Checking SSH key pair..."
if [ -f ~/.ssh/hostaway-deploy ] && [ -f ~/.ssh/hostaway-deploy.pub ]; then
  echo "  ✅ SSH key pair found"

  # Check permissions
  PRIV_PERMS=$(stat -f "%Lp" ~/.ssh/hostaway-deploy 2>/dev/null || stat -c "%a" ~/.ssh/hostaway-deploy 2>/dev/null)
  if [ "$PRIV_PERMS" != "600" ]; then
    echo "  ⚠️  WARNING: Private key permissions should be 600, found $PRIV_PERMS"
    echo "     Run: chmod 600 ~/.ssh/hostaway-deploy"
    WARNINGS=$((WARNINGS + 1))
  fi
else
  echo "  ❌ SSH key pair NOT found at ~/.ssh/hostaway-deploy"
  echo "     Run: ssh-keygen -t ed25519 -C \"github-actions\" -f ~/.ssh/hostaway-deploy"
  ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 2: SSH connection to Hostinger
echo "✓ Testing SSH connection to Hostinger..."
if ssh -i ~/.ssh/hostaway-deploy -o ConnectTimeout=5 -o StrictHostKeyChecking=no root@72.60.233.157 "echo 'Connection successful'" 2>/dev/null | grep -q "Connection successful"; then
  echo "  ✅ SSH connection to Hostinger successful"
else
  echo "  ❌ SSH connection to Hostinger FAILED"
  echo "     Verify public key is in /root/.ssh/authorized_keys on Hostinger"
  echo "     Test manually: ssh -i ~/.ssh/hostaway-deploy root@72.60.233.157"
  ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 3: Deployment directory exists on Hostinger
echo "✓ Checking deployment directory on Hostinger..."
if ssh -i ~/.ssh/hostaway-deploy -o ConnectTimeout=5 root@72.60.233.157 "[ -d /opt/hostaway-mcp ] && echo 'exists'" 2>/dev/null | grep -q "exists"; then
  echo "  ✅ Deployment directory /opt/hostaway-mcp exists"
else
  echo "  ⚠️  WARNING: Deployment directory /opt/hostaway-mcp NOT found"
  echo "     This may be expected if not yet created"
  WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check 4: Docker and docker-compose on Hostinger
echo "✓ Checking Docker installation on Hostinger..."
if ssh -i ~/.ssh/hostaway-deploy -o ConnectTimeout=5 root@72.60.233.157 "command -v docker" 2>/dev/null | grep -q "docker"; then
  echo "  ✅ Docker installed on Hostinger"
else
  echo "  ❌ Docker NOT found on Hostinger"
  ERRORS=$((ERRORS + 1))
fi

if ssh -i ~/.ssh/hostaway-deploy -o ConnectTimeout=5 root@72.60.233.157 "command -v docker-compose || docker compose version" 2>/dev/null | grep -q "compose"; then
  echo "  ✅ docker-compose available on Hostinger"
else
  echo "  ⚠️  WARNING: docker-compose NOT found on Hostinger"
  WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check 5: GitHub Secrets (can't verify values, just check if file exists)
echo "✓ GitHub Secrets Configuration..."
echo "  ⚠️  Cannot verify GitHub Secrets programmatically"
echo "     Please verify manually at:"
echo "     https://github.com/[ORG]/[REPO]/settings/secrets/actions"
echo ""
echo "  Required secrets (9 total):"
echo "    - SSH_PRIVATE_KEY"
echo "    - SSH_HOST"
echo "    - SSH_USERNAME"
echo "    - DEPLOY_PATH"
echo "    - SUPABASE_URL"
echo "    - SUPABASE_SERVICE_KEY"
echo "    - SUPABASE_ANON_KEY"
echo "    - HOSTAWAY_ACCOUNT_ID"
echo "    - HOSTAWAY_SECRET_KEY"
echo ""

# Check 6: No secrets in git history
echo "✓ Checking for leaked secrets in git history..."
if git log --all -S "BEGIN OPENSSH PRIVATE KEY" | grep -q "BEGIN OPENSSH"; then
  echo "  ❌ SECURITY RISK: Private key found in git history!"
  echo "     This requires immediate cleanup"
  ERRORS=$((ERRORS + 1))
else
  echo "  ✅ No private keys found in git history"
fi
echo ""

# Summary
echo "=================================================="
echo "Verification Summary"
echo "=================================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo "✅ All checks passed! Ready to proceed to Phase 3"
  echo ""
  echo "Next steps:"
  echo "  1. Mark tasks T003-T015 as complete in tasks.md"
  echo "  2. Proceed to Phase 3: User Story 1 implementation"
  exit 0
elif [ $ERRORS -eq 0 ]; then
  echo "⚠️  $WARNINGS warning(s) found - review above"
  echo "   Setup is functional but should be reviewed"
  exit 0
else
  echo "❌ $ERRORS error(s) and $WARNINGS warning(s) found"
  echo "   Fix errors before proceeding to Phase 3"
  exit 1
fi
