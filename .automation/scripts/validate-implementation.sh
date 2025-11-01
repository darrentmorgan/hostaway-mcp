#!/usr/bin/env bash
# Validation Script for Automation Implementation
# Verifies all components are correctly implemented

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../config"
LOGS_DIR="${SCRIPT_DIR}/../logs"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Check function
check() {
    local description="$1"
    local command="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "  Checking: ${description}... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

echo "========================================="
echo "Automation Implementation Validation"
echo "========================================="
echo ""

# Phase 1: Directory Structure
echo "Phase 1: Directory Structure"
echo "----------------------------"
check "Config directory exists" "test -d '$CONFIG_DIR'"
check "Scripts directory exists" "test -d '$SCRIPT_DIR'"
check "Logs directory exists" "test -d '$LOGS_DIR'"
check "Templates directory exists" "test -d '$SCRIPT_DIR/../templates'"
echo ""

# Phase 2: Configuration Files
echo "Phase 2: Configuration Files"
echo "-----------------------------"
check "dependency-graph.yaml exists" "test -f '$CONFIG_DIR/dependency-graph.yaml'"
check "fix-definitions.yaml exists" "test -f '$CONFIG_DIR/fix-definitions.yaml'"
check "worktree-config.yaml exists" "test -f '$CONFIG_DIR/worktree-config.yaml'"
check "dependency-graph.yaml is valid YAML" "python3 -c 'import yaml; yaml.safe_load(open(\"$CONFIG_DIR/dependency-graph.yaml\"))'"
check "fix-definitions.yaml is valid YAML" "python3 -c 'import yaml; yaml.safe_load(open(\"$CONFIG_DIR/fix-definitions.yaml\"))'"
check "worktree-config.yaml is valid YAML" "python3 -c 'import yaml; yaml.safe_load(open(\"$CONFIG_DIR/worktree-config.yaml\"))'"
echo ""

# Phase 3: Core Scripts
echo "Phase 3: Core Scripts"
echo "---------------------"
check "orchestrator.sh exists and is executable" "test -x '$SCRIPT_DIR/orchestrator.sh'"
check "worktree-manager.sh exists and is executable" "test -x '$SCRIPT_DIR/worktree-manager.sh'"
check "fix-executor.sh exists and is executable" "test -x '$SCRIPT_DIR/fix-executor.sh'"
check "test-runner.sh exists and is executable" "test -x '$SCRIPT_DIR/test-runner.sh'"
check "pr-automation.sh exists and is executable" "test -x '$SCRIPT_DIR/pr-automation.sh'"
check "status.sh exists and is executable" "test -x '$SCRIPT_DIR/status.sh'"
check "generate-report.sh exists and is executable" "test -x '$SCRIPT_DIR/generate-report.sh'"
check "rollback.sh exists and is executable" "test -x '$SCRIPT_DIR/rollback.sh'"
check "cleanup.sh exists and is executable" "test -x '$SCRIPT_DIR/cleanup.sh'"
check "validate-config.sh exists and is executable" "test -x '$SCRIPT_DIR/validate-config.sh'"
check "state_manager.py exists and is executable" "test -x '$SCRIPT_DIR/state_manager.py'"
echo ""

# Phase 4: Templates
echo "Phase 4: Templates"
echo "------------------"
check "fix-template.j2 exists" "test -f '$SCRIPT_DIR/../templates/fix-template.j2'"
check "test-template.j2 exists" "test -f '$SCRIPT_DIR/../templates/test-template.j2'"
echo ""

# Phase 5: Error Handling
echo "Phase 5: Error Handling"
echo "-----------------------"
check "All bash scripts use 'set -euo pipefail'" "grep -l 'set -euo pipefail' $SCRIPT_DIR/*.sh | wc -l | grep -q 11"
check "orchestrator.sh has trap handler" "grep -q 'trap.*cleanup_on_exit.*EXIT' '$SCRIPT_DIR/orchestrator.sh'"
echo ""

# Phase 6: Test Files
echo "Phase 6: Test Files"
echo "-------------------"
check "test_dependency_resolver.py exists" "test -f '$(dirname $SCRIPT_DIR)/../tests/automation/test_dependency_resolver.py'"
check "test_rollback.py exists" "test -f '$(dirname $SCRIPT_DIR)/../tests/automation/test_rollback.py'"
check "test_mcp_stdio_improvements.py exists" "test -f '$(dirname $SCRIPT_DIR)/../tests/mcp/test_mcp_stdio_improvements.py'"
check "test_integration_all_fixes.py exists" "test -f '$(dirname $SCRIPT_DIR)/../tests/mcp/test_integration_all_fixes.py'"
echo ""

# Phase 7: Documentation
echo "Phase 7: Documentation"
echo "----------------------"
check ".automation/README.md exists" "test -f '$SCRIPT_DIR/../README.md'"
check "Project README.md has automation section" "grep -q 'Automated MCP Migration' '$(dirname $SCRIPT_DIR)/../README.md'"
check ".dockerignore exists" "test -f '$SCRIPT_DIR/../.dockerignore'"
echo ""

# Phase 8: Script Functionality
echo "Phase 8: Script Functionality"
echo "------------------------------"
check "orchestrator.sh --help works" "$SCRIPT_DIR/orchestrator.sh --help"
check "status.sh --help works" "$SCRIPT_DIR/status.sh --help"
check "rollback.sh --help works" "$SCRIPT_DIR/rollback.sh --help"
check "generate-report.sh --help works" "$SCRIPT_DIR/generate-report.sh --help"
check "cleanup.sh --help works" "$SCRIPT_DIR/cleanup.sh --help"
check "validate-config.sh works" "$SCRIPT_DIR/validate-config.sh"
echo ""

# Phase 9: Python Dependencies
echo "Phase 9: Python Dependencies"
echo "----------------------------"
check "PyYAML is importable" "python3 -c 'import yaml'"
check "json module available" "python3 -c 'import json'"
check "pathlib available" "python3 -c 'from pathlib import Path'"
echo ""

# Phase 10: Git Configuration
echo "Phase 10: Git Configuration"
echo "---------------------------"
check "Git repository exists" "git rev-parse --git-dir"
check "Git version >= 2.30" "git version | grep -oE '[0-9]+\.[0-9]+' | head -1 | awk '{if (\$1 >= 2.30) exit 0; else exit 1}'"
check "Git worktree command available" "git worktree --help"
echo ""

# Summary
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo ""
echo "Total Checks: ${TOTAL_CHECKS}"
echo -e "Passed: ${GREEN}${PASSED_CHECKS}${NC}"
echo -e "Failed: ${RED}${FAILED_CHECKS}${NC}"
echo ""

if [[ $FAILED_CHECKS -eq 0 ]]; then
    echo -e "${GREEN}✅ All validation checks passed!${NC}"
    echo ""
    echo "The automated MCP migration system is ready to use."
    echo ""
    echo "Next steps:"
    echo "  1. Review the execution plan:"
    echo "     .automation/scripts/orchestrator.sh --dry-run"
    echo ""
    echo "  2. Execute the migration:"
    echo "     .automation/scripts/orchestrator.sh --auto-rollback"
    echo ""
    echo "  3. Monitor progress:"
    echo "     .automation/scripts/status.sh --watch"
    echo ""
    exit 0
else
    echo -e "${RED}❌ ${FAILED_CHECKS} validation check(s) failed${NC}"
    echo ""
    echo "Please review the failed checks above and fix any issues."
    echo ""
    exit 1
fi
