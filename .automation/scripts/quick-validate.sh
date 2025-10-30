#!/usr/bin/env bash
# Quick Deployment Validation
# Fast pre-deployment checks without running full test suite

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "Quick Deployment Validation"
echo "========================================="
echo ""

PASSED=0
FAILED=0
WARNINGS=0

# Git status
echo "1. Git Status"
echo "   Branch: $(git rev-parse --abbrev-ref HEAD)"

if git diff --quiet; then
    echo -e "   ${GREEN}✓${NC} No uncommitted changes"
    PASSED=$((PASSED + 1))
else
    echo -e "   ${YELLOW}⚠${NC} Uncommitted changes present"
    git status --short | head -5
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# Code quality
echo "2. Code Quality"
if command -v uv &>/dev/null; then
    if uv run ruff format --check src/ tests/ --quiet 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} Formatting passed"
        PASSED=$((PASSED + 1))
    else
        echo -e "   ${RED}✗${NC} Formatting issues"
        FAILED=$((FAILED + 1))
    fi

    if uv run ruff check src/ tests/ --quiet 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} Linting passed"
        PASSED=$((PASSED + 1))
    else
        echo -e "   ${YELLOW}⚠${NC} Linting warnings"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "   ${YELLOW}⚠${NC} uv not available - skipping"
fi

echo ""

# Docker build check
echo "3. Build Check"
if [[ -f Dockerfile ]]; then
    echo -n "   Docker build... "
    if docker build -t hostaway-mcp:quick-check . -q > /tmp/docker-build.log 2>&1; then
        echo -e "${GREEN}✓${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC}"
        echo "   Last 10 lines of build log:"
        tail -10 /tmp/docker-build.log | sed 's/^/   /'
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "   ${YELLOW}⚠${NC} No Dockerfile"
fi

echo ""

# Deployment readiness
echo "4. Deployment"
if curl -sf http://72.60.233.157:8080/health > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Production server healthy"
    PASSED=$((PASSED + 1))
else
    echo -e "   ${YELLOW}⚠${NC} Cannot reach production"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo -e "Warnings: ${YELLOW}${WARNINGS}${NC}"
echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}✅ Ready for deployment${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Commit changes: git add . && git commit -m 'message'"
    echo "  2. Push: git push origin $(git rev-parse --abbrev-ref HEAD)"
    echo "  3. Create PR: gh pr create --fill"
    exit 0
else
    echo -e "${RED}❌ Fix issues before deployment${NC}"
    exit 1
fi
