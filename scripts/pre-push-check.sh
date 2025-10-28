#!/bin/bash
# Pre-push validation script
# Runs all linting and checks before pushing to CI/CD
# Usage: ./scripts/pre-push-check.sh

set -e  # Exit on first error

echo "🔍 Running pre-push validation checks..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Function to run a check and track failures
run_check() {
    local check_name="$1"
    local check_cmd="$2"

    echo -e "${YELLOW}▶ ${check_name}${NC}"
    if eval "$check_cmd"; then
        echo -e "${GREEN}✓ ${check_name} passed${NC}"
        echo ""
    else
        echo -e "${RED}✗ ${check_name} failed${NC}"
        echo ""
        FAILURES=$((FAILURES + 1))
    fi
}

# 1. Ruff Format Check
run_check "Ruff Format Check" "uv run ruff format --check ."

# 2. Ruff Lint Check
run_check "Ruff Lint Check" "uv run ruff check ."

# 3. Quick Integration Tests (no coverage - just verify tests pass)
echo -e "${YELLOW}▶ Quick Integration Tests${NC}"
echo "Running fast integration tests (no coverage)..."
if uv run pytest tests/integration/ -q --tb=short -x --no-cov; then
    echo -e "${GREEN}✓ Quick Integration Tests passed${NC}"
    echo ""
else
    echo -e "${RED}✗ Quick Integration Tests failed${NC}"
    echo ""
    FAILURES=$((FAILURES + 1))
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All pre-push checks passed!${NC}"
    echo -e "${GREEN}✓ Safe to push to CI/CD${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILURES check(s) failed${NC}"
    echo -e "${RED}✗ DO NOT push to CI/CD until issues are resolved${NC}"
    exit 1
fi
