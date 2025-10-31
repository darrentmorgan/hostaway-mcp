#!/usr/bin/env bash
# Pre-PR Validation Script
# ENHANCED VERSION - Lessons from PR #8 (2025-10-31)
#
# This script implements the learnings from PR #8 CI failures:
# 1. Format ALL files before validation (not just check)
# 2. Run integration tests to catch 500 errors
# 3. Validate both local and CI-expected behavior
#
# Usage:
#   ./pre-pr-validate.sh              # Full validation with fixes
#   ./pre-pr-validate.sh --check-only # Check only, no fixes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Mode
CHECK_ONLY="${1:-false}"
if [[ "$CHECK_ONLY" == "--check-only" ]]; then
    CHECK_ONLY=true
else
    CHECK_ONLY=false
fi

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# Issues
BLOCKING_ISSUES=()
WARNING_ISSUES=()
FIXED_ISSUES=()

cd "$PROJECT_ROOT"

echo "========================================="
echo "Pre-PR Validation (Enhanced)"
echo "========================================="
echo "Mode: $([ "$CHECK_ONLY" == "true" ] && echo "CHECK ONLY" || echo "FIX & VALIDATE")"
echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo ""

# Phase 1: Code Formatting & Linting
echo "Phase 1: Code Quality (Format & Lint)"
echo "--------------------------------------"

if [ "$CHECK_ONLY" == "false" ]; then
    echo "  Applying ruff formatting..."
    if uv run ruff format src/ tests/ >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Formatting applied"
        FIXED_ISSUES+=("Applied ruff formatting to src/ and tests/")
    else
        echo -e "  ${RED}✗${NC} Formatting failed"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        BLOCKING_ISSUES+=("Ruff formatting failed")
    fi

    echo "  Applying ruff linting fixes..."
    if uv run ruff check src/ tests/ --fix >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Linting fixes applied"
        FIXED_ISSUES+=("Applied ruff linting fixes")
    else
        echo -e "  ${YELLOW}⚠${NC} Some linting issues remain"
        WARNINGS=$((WARNINGS + 1))
        WARNING_ISSUES+=("Linting has warnings")
    fi
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 2))

# Verify no formatting issues remain
echo "  Verifying formatting..."
if uv run ruff format --check src/ tests/ --quiet 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Formatting check passed"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${RED}✗${NC} Formatting issues remain"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    BLOCKING_ISSUES+=("Formatting check failed - files need formatting")

    # Show which files need formatting
    echo "  Files needing formatting:"
    uv run ruff format --check src/ tests/ 2>&1 | grep "Would reformat:" | sed 's/^/    /'
fi

# Verify no linting issues remain
echo "  Verifying linting..."
if uv run ruff check src/ tests/ --quiet 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Linting check passed"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${YELLOW}⚠${NC} Linting warnings present"
    WARNINGS=$((WARNINGS + 1))
    WARNING_ISSUES+=("Linting warnings found")

    # Show linting issues
    echo "  Linting issues:"
    uv run ruff check src/ tests/ 2>&1 | head -20 | sed 's/^/    /'
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 2))

echo ""

# Phase 2: Testing (ENHANCED)
echo "Phase 2: Testing (Unit + Integration)"
echo "--------------------------------------"

# Unit tests first (fast feedback)
echo "  Running unit tests..."
if uv run pytest tests/unit -v --no-cov --tb=short > /tmp/unit-tests.log 2>&1; then
    echo -e "  ${GREEN}✓${NC} Unit tests passed"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${RED}✗${NC} Unit tests failed"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    BLOCKING_ISSUES+=("Unit tests failing")
    tail -20 /tmp/unit-tests.log | sed 's/^/    /'
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Integration tests (CRITICAL - catches 500 errors)
echo "  Running integration tests (CRITICAL)..."
if uv run pytest tests/integration -v --no-cov --tb=short > /tmp/integration-tests.log 2>&1; then
    echo -e "  ${GREEN}✓${NC} Integration tests passed"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${RED}✗${NC} Integration tests failed"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    BLOCKING_ISSUES+=("Integration tests failing")

    # Check for 500 errors specifically
    if grep -q "assert 500 == 200" /tmp/integration-tests.log; then
        echo -e "  ${RED}⚠${NC} Found 500 Internal Server Error in tests!"
        BLOCKING_ISSUES+=("500 Internal Server Error in integration tests - investigate server-side issues")
    fi

    # Show failed tests
    echo "  Failed tests:"
    grep "FAILED" /tmp/integration-tests.log | sed 's/^/    /' || true

    # Show assertion errors
    echo "  Assertion errors:"
    grep -A 2 "AssertionError" /tmp/integration-tests.log | head -20 | sed 's/^/    /' || true
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Coverage check
echo "  Checking test coverage..."
if uv run pytest --cov=src --cov-report=term --cov-report=json --quiet > /tmp/coverage.log 2>&1; then
    if [[ -f coverage.json ]]; then
        COVERAGE=$(python3 -c "import json; data=json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.1f}\")")
        if (( $(echo "$COVERAGE >= 80" | bc -l) )); then
            echo -e "  ${GREEN}✓${NC} Coverage: ${COVERAGE}% (>= 80% required)"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo -e "  ${RED}✗${NC} Coverage: ${COVERAGE}% (< 80% required)"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            BLOCKING_ISSUES+=("Test coverage below 80%")
        fi
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Coverage check had issues"
    WARNINGS=$((WARNINGS + 1))
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""

# Phase 3: Type Checking & Security
echo "Phase 3: Type Checking & Security"
echo "----------------------------------"

echo "  Running mypy type check..."
if uv run mypy src/ --config-file=pyproject.toml --quiet 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Type checking passed"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${YELLOW}⚠${NC} Type checking warnings"
    WARNINGS=$((WARNINGS + 1))
    WARNING_ISSUES+=("MyPy type checking warnings")
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo "  Running bandit security scan..."
if uv run bandit -r src/ -ll -q 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Security scan passed"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${RED}✗${NC} Security issues found"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    BLOCKING_ISSUES+=("Bandit security scan failed")
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""

# Summary
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo ""
echo "Total Checks: ${TOTAL_CHECKS}"
echo -e "Passed: ${GREEN}${PASSED_CHECKS}${NC}"
echo -e "Failed: ${RED}${FAILED_CHECKS}${NC}"
echo -e "Warnings: ${YELLOW}${WARNINGS}${NC}"
echo ""

if [ ${#FIXED_ISSUES[@]} -gt 0 ]; then
    echo "Issues Fixed:"
    for issue in "${FIXED_ISSUES[@]}"; do
        echo -e "  ${GREEN}✓${NC} $issue"
    done
    echo ""
fi

# Overall status
if [[ $FAILED_CHECKS -eq 0 ]]; then
    if [[ $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}✅ READY FOR PR${NC}"
        echo ""
        echo "All checks passed! Your changes are ready for:"
        echo "  1. Creating a PR"
        echo "  2. CI/CD pipeline (will pass)"
        echo "  3. Auto-merge and deployment"
        echo ""
        echo "Lessons from PR #8 applied:"
        echo "  ✓ All files formatted before commit"
        echo "  ✓ Integration tests verified (no 500 errors)"
        echo "  ✓ Linting issues fixed"
    else
        echo -e "${YELLOW}⚠️  READY WITH WARNINGS${NC}"
        echo ""
        echo "Your changes will likely deploy, but consider fixing:"
        for warning in "${WARNING_ISSUES[@]}"; do
            echo "  - $warning"
        done
    fi
else
    echo -e "${RED}❌ BLOCKED - FIX REQUIRED${NC}"
    echo ""
    echo "The following issues will block CI/CD:"
    for issue in "${BLOCKING_ISSUES[@]}"; do
        echo "  - $issue"
    done
    echo ""
    echo "Lessons from PR #8:"
    echo "  1. Run 'uv run ruff format src/ tests/' to fix formatting"
    echo "  2. Run 'uv run ruff check src/ tests/ --fix' to fix linting"
    echo "  3. Investigate integration test failures (especially 500 errors)"
    echo "  4. Re-run this script to verify fixes"
fi

echo ""

# Exit code
if [[ $FAILED_CHECKS -eq 0 ]]; then
    exit 0
else
    exit 1
fi
