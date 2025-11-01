#!/usr/bin/env bash
# Pre-Push Validation Script
# Ensures code quality before pushing to remote

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${PROJECT_ROOT}"

echo "🔍 Running pre-push validation..."
echo ""

# Check 1: Code formatting
echo "1️⃣  Checking code formatting..."
if uv run ruff format --check src/ tests/; then
    echo "   ✅ Formatting OK"
else
    echo "   ❌ Formatting failed"
    echo "   Fix with: uv run ruff format src/ tests/"
    exit 1
fi
echo ""

# Check 2: Linting
echo "2️⃣  Running linter..."
if uv run ruff check src/ tests/; then
    echo "   ✅ Linting OK"
else
    echo "   ❌ Linting failed"
    echo "   Fix with: uv run ruff check src/ tests/ --fix"
    exit 1
fi
echo ""

# Check 3: Type checking
echo "3️⃣  Running type checker..."
if uv run mypy src/ tests/ --strict; then
    echo "   ✅ Type checking OK"
else
    echo "   ❌ Type checking failed"
    echo "   Review type errors and fix them"
    exit 1
fi
echo ""

# Check 4: Security audit
echo "4️⃣  Running security audit..."
if uv run bandit -r src/ -ll; then
    echo "   ✅ Security audit OK"
else
    echo "   ❌ Security issues found"
    echo "   Review and fix security vulnerabilities"
    exit 1
fi
echo ""

# Check 5: Unit tests
echo "5️⃣  Running unit tests..."
if uv run pytest tests/unit/ -v --no-cov -x; then
    echo "   ✅ Unit tests OK"
else
    echo "   ❌ Unit tests failed"
    echo "   Fix failing tests before pushing"
    exit 1
fi
echo ""

# Check 6: Integration tests (quick subset)
echo "6️⃣  Running integration tests..."
if uv run pytest tests/integration/ -v --no-cov -x -m "not slow"; then
    echo "   ✅ Integration tests OK"
else
    echo "   ❌ Integration tests failed"
    echo "   Fix failing tests before pushing"
    exit 1
fi
echo ""

# Check 7: Test coverage
echo "7️⃣  Checking test coverage..."
coverage_output=$(uv run pytest tests/ --cov=src --cov-report=term 2>&1 || true)
coverage_percent=$(echo "$coverage_output" | grep "TOTAL" | awk '{print $4}' | sed 's/%//')

if [ -n "$coverage_percent" ] && [ "$(echo "$coverage_percent >= 80" | bc)" -eq 1 ]; then
    echo "   ✅ Test coverage OK (${coverage_percent}%)"
else
    echo "   ⚠️  Test coverage below 80% (${coverage_percent}%)"
    echo "   Warning: This may cause CI to fail"
    echo "   Add tests to improve coverage"
fi
echo ""

echo "✅ All pre-push checks passed!"
echo ""
echo "Safe to push:"
echo "  git push origin \$(git branch --show-current)"
echo ""
