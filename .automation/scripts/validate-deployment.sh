#!/usr/bin/env bash
# Deployment Validation Script
# Validates code changes are ready for CI/CD auto-merge and Hostinger VPS deployment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# Status tracking
BLOCKING_ISSUES=()
WARNING_ISSUES=()
RECOMMENDATIONS=()

# Check function
check() {
    local description="$1"
    local command="$2"
    local is_critical="${3:-true}"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "  ${description}... "

    local output
    if output=$(eval "$command" 2>&1); then
        echo -e "${GREEN}✓${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        if [[ "$is_critical" == "true" ]]; then
            echo -e "${RED}✗${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            BLOCKING_ISSUES+=("$description")
        else
            echo -e "${YELLOW}⚠${NC}"
            WARNINGS=$((WARNINGS + 1))
            WARNING_ISSUES+=("$description")
        fi
        echo "    Error: $output" | head -3
        return 1
    fi
}

echo "========================================="
echo "Deployment Validation Report"
echo "========================================="
echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo ""

# Phase 1: Git Status
echo "Phase 1: Git & Branch Status"
echo "-----------------------------"
check "Git repository is valid" "git rev-parse --git-dir"
check "No uncommitted changes" "test -z \"\$(git status --porcelain)\"" "false"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "  Current branch: ${CURRENT_BRANCH}"

if git diff --quiet HEAD origin/"${CURRENT_BRANCH}" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Branch is up-to-date with remote"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${YELLOW}⚠${NC} Branch differs from remote"
    WARNING_ISSUES+=("Branch needs push or pull")
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""

# Phase 2: Code Quality
echo "Phase 2: Code Quality Checks"
echo "-----------------------------"

cd "$PROJECT_ROOT"

# Check if ruff is available
if command -v uv &>/dev/null; then
    check "Ruff format check" "uv run ruff format --check src/ tests/ --quiet"
    check "Ruff linting" "uv run ruff check src/ tests/"
    check "MyPy type checking" "uv run mypy src/ --config-file=pyproject.toml" "false"
    check "Bandit security scan" "uv run bandit -r src/ -ll -q"
else
    echo -e "  ${YELLOW}⚠${NC} uv not found - skipping quality checks"
    WARNING_ISSUES+=("uv package manager not installed")
fi

echo ""

# Phase 3: Test Coverage
echo "Phase 3: Test Coverage"
echo "----------------------"

if command -v uv &>/dev/null; then
    echo "  Running pytest with coverage..."

    if uv run pytest --cov=src --cov-report=term --cov-report=json --quiet 2>&1 | tee /tmp/pytest-output.txt; then
        echo -e "  ${GREEN}✓${NC} All tests passed"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))

        # Check coverage
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
            TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        fi
    else
        echo -e "  ${RED}✗${NC} Tests failed"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        BLOCKING_ISSUES+=("Pytest tests failing")
        cat /tmp/pytest-output.txt | tail -20
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
else
    echo -e "  ${YELLOW}⚠${NC} Cannot run tests without uv"
fi

echo ""

# Phase 4: Build Validation
echo "Phase 4: Build & Dependencies"
echo "------------------------------"

check "pyproject.toml exists" "test -f pyproject.toml"
check "uv.lock is committed" "git ls-files --error-unmatch uv.lock"

if [[ -f Dockerfile ]]; then
    echo "  Checking Docker build..."
    if docker build -t hostaway-mcp:validation-test . -q > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Docker build succeeds"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "  ${RED}✗${NC} Docker build failed"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        BLOCKING_ISSUES+=("Docker build failing")
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

if [[ -f docker-compose.yml ]]; then
    check "docker-compose.yml is valid" "docker-compose config" "false"
fi

echo ""

# Phase 5: CI/CD Requirements
echo "Phase 5: CI/CD Requirements"
echo "---------------------------"

CI_WORKFLOW=".github/workflows/ci-cd.yml"
if [[ -f "$CI_WORKFLOW" ]]; then
    echo -e "  ${GREEN}✓${NC} CI/CD workflow exists"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))

    # Check workflow steps
    echo "  Validating workflow steps:"
    if grep -q "ruff" "$CI_WORKFLOW"; then
        echo -e "    ${GREEN}✓${NC} Linting step present"
    else
        echo -e "    ${YELLOW}⚠${NC} No linting step found"
        WARNING_ISSUES+=("CI workflow missing linting")
    fi

    if grep -q "pytest" "$CI_WORKFLOW"; then
        echo -e "    ${GREEN}✓${NC} Test step present"
    else
        echo -e "    ${RED}✗${NC} No test step found"
        BLOCKING_ISSUES+=("CI workflow missing tests")
    fi

    if grep -q "mypy" "$CI_WORKFLOW"; then
        echo -e "    ${GREEN}✓${NC} Type check step present"
    else
        echo -e "    ${YELLOW}⚠${NC} No type check step found"
        WARNING_ISSUES+=("CI workflow missing type checks")
    fi
else
    echo -e "  ${RED}✗${NC} CI/CD workflow not found"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    BLOCKING_ISSUES+=("No CI/CD workflow configured")
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""

# Phase 6: Deployment Readiness (Hostinger VPS)
echo "Phase 6: Deployment Readiness"
echo "------------------------------"

# Check if deployment config exists
if [[ -f docker-compose.prod.yml ]]; then
    echo -e "  ${GREEN}✓${NC} Production docker-compose found"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))

    # Validate production config
    if docker-compose -f docker-compose.prod.yml config > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Production config is valid"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "  ${RED}✗${NC} Production config invalid"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        BLOCKING_ISSUES+=("docker-compose.prod.yml has errors")
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
else
    echo -e "  ${YELLOW}⚠${NC} No docker-compose.prod.yml found"
    WARNING_ISSUES+=("No production docker-compose config")
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Check health endpoint
echo "  Checking production health endpoint..."
if curl -s -f http://72.60.233.157:8080/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Production server is healthy"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${YELLOW}⚠${NC} Cannot reach production server"
    WARNING_ISSUES+=("Production server unreachable or unhealthy")
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""

# Phase 7: Auto-Merge Criteria
echo "Phase 7: Auto-Merge Readiness"
echo "------------------------------"

# Check if on feature branch
if [[ "$CURRENT_BRANCH" == "main" ]] || [[ "$CURRENT_BRANCH" == "master" ]]; then
    echo -e "  ${RED}✗${NC} Cannot auto-merge from main/master branch"
    BLOCKING_ISSUES+=("Must be on feature branch for auto-merge")
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    echo -e "  ${GREEN}✓${NC} On feature branch: ${CURRENT_BRANCH}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Check commit messages
echo "  Checking commit messages..."
INVALID_COMMITS=$(git log --oneline origin/main..HEAD --grep="^WIP\|^TODO\|^FIXME" || true)
if [[ -z "$INVALID_COMMITS" ]]; then
    echo -e "  ${GREEN}✓${NC} No WIP/TODO commits"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "  ${YELLOW}⚠${NC} Found WIP/TODO commits"
    WARNING_ISSUES+=("Commit messages contain WIP/TODO")
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

# Overall status
if [[ $FAILED_CHECKS -eq 0 ]]; then
    if [[ $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}✅ READY FOR DEPLOYMENT${NC}"
        echo ""
        echo "All checks passed! Your changes are ready for:"
        echo "  1. Creating a PR"
        echo "  2. Auto-merge after CI passes"
        echo "  3. Automatic deployment to Hostinger VPS"
        echo ""
        echo "Next steps:"
        echo "  git push origin ${CURRENT_BRANCH}"
        echo "  gh pr create --fill --label auto-merge"
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
    echo "The following issues will block deployment:"
    for issue in "${BLOCKING_ISSUES[@]}"; do
        echo "  - $issue"
    done
    echo ""
    echo "Fix these issues before creating a PR."
fi

echo ""

# Detailed recommendations
if [[ ${#BLOCKING_ISSUES[@]} -gt 0 ]] || [[ ${#WARNING_ISSUES[@]} -gt 0 ]]; then
    echo "========================================="
    echo "Recommended Actions"
    echo "========================================="

    if [[ ${#BLOCKING_ISSUES[@]} -gt 0 ]]; then
        echo ""
        echo "BLOCKING ISSUES (must fix):"
        for issue in "${BLOCKING_ISSUES[@]}"; do
            echo "  🔴 $issue"

            # Provide specific fix suggestions
            case "$issue" in
                *"coverage"*)
                    echo "     → Add more tests or remove dead code"
                    ;;
                *"tests failing"*)
                    echo "     → Run: uv run pytest -v to see failures"
                    ;;
                *"Docker build"*)
                    echo "     → Run: docker build . to see build errors"
                    ;;
                *"uncommitted"*)
                    echo "     → Run: git add . && git commit -m 'message'"
                    ;;
            esac
        done
    fi

    if [[ ${#WARNING_ISSUES[@]} -gt 0 ]]; then
        echo ""
        echo "WARNINGS (should fix):"
        for warning in "${WARNING_ISSUES[@]}"; do
            echo "  🟡 $warning"
        done
    fi

    echo ""
fi

# Exit code
if [[ $FAILED_CHECKS -eq 0 ]]; then
    exit 0
else
    exit 1
fi
