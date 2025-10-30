#!/usr/bin/env bash
# Test Runner for MCP Migration Fixes
# Runs pytest unit tests and MCP Inspector validation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../config"
LOGS_DIR="${SCRIPT_DIR}/../logs"

# Usage information
usage() {
    cat <<EOF
Usage: $(basename "$0") <fix_id>

Run tests for a specific fix within its worktree.

Arguments:
    fix_id          Fix identifier (e.g., fix-1-service-prefixes)

Options:
    -h, --help      Show this help message

Examples:
    $(basename "$0") fix-1-service-prefixes
    $(basename "$0") fix-3-error-messages
EOF
}

# Load fix definition
get_test_file() {
    local fix_id="$1"

    python3 <<EOF
import yaml

with open("${CONFIG_DIR}/fix-definitions.yaml") as f:
    definitions = yaml.safe_load(f)

fix_def = next((f for f in definitions["fixes"] if f["fix_id"] == "${fix_id}"), None)

if fix_def:
    print(fix_def["test_file"])
else:
    print("", end="")
EOF
}

# Run unit tests
run_unit_tests() {
    local fix_id="$1"
    local worktree_path="$2"

    echo "Running unit tests for ${fix_id}..."

    cd "${worktree_path}"

    # Get test file for this fix
    local test_file
    test_file=$(get_test_file "${fix_id}")

    if [[ -z "$test_file" ]]; then
        echo "  ! No test file specified for ${fix_id}"
        return 0
    fi

    if [[ ! -f "$test_file" ]]; then
        echo "  ! Test file not found: ${test_file}"
        echo "  ! Skipping unit tests"
        return 0
    fi

    echo "  Running pytest on ${test_file}..."

    if uv run pytest "${test_file}" -v --tb=short; then
        echo "  ✓ Unit tests passed"
        return 0
    else
        echo "  ✗ Unit tests failed"
        return 1
    fi
}

# Run MCP Inspector validation
run_mcp_inspector() {
    local fix_id="$1"
    local worktree_path="$2"

    echo "Running MCP Inspector validation..."

    cd "${worktree_path}"

    # Check if MCP Inspector is available
    if ! command -v npx &>/dev/null; then
        echo "  ! npx not found, skipping MCP Inspector validation"
        return 0
    fi

    # First verify the module imports correctly
    echo "  Checking MCP stdio server import..."
    if ! python3 -c "import mcp_stdio_server" 2>/dev/null; then
        echo "  ✗ MCP stdio server has import errors"
        return 1
    fi
    echo "  ✓ MCP stdio server imports successfully"

    # Run MCP Inspector to validate tool schemas
    echo "  Running MCP Inspector validation..."

    # Create temporary config for MCP Inspector
    local inspector_config="/tmp/mcp-inspector-${fix_id}.json"
    cat > "${inspector_config}" <<EOF
{
  "mcpServers": {
    "hostaway": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_stdio_server"]
    }
  }
}
EOF

    # Run MCP Inspector with validation
    # This validates:
    # - Tool schemas are valid JSON Schema
    # - All required fields are present
    # - Enum values are properly defined
    # - Type constraints are correct
    if npx -y @modelcontextprotocol/inspector@latest \
        --config "${inspector_config}" \
        --server hostaway \
        --validate-only 2>&1 | tee "${LOGS_DIR}/mcp-inspector-${fix_id}.log"; then
        echo "  ✓ MCP Inspector validation passed"
        rm -f "${inspector_config}"
        return 0
    else
        echo "  ✗ MCP Inspector validation failed"
        echo "  See logs at: ${LOGS_DIR}/mcp-inspector-${fix_id}.log"
        rm -f "${inspector_config}"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    local fix_id="$1"
    local worktree_path="$2"

    echo "Running integration tests..."

    cd "${worktree_path}"

    # Run integration tests if they exist
    if [[ -d "tests/integration" ]]; then
        echo "  Running integration test suite..."

        if uv run pytest tests/integration -v --tb=short -m "not e2e"; then
            echo "  ✓ Integration tests passed"
            return 0
        else
            echo "  ✗ Integration tests failed"
            return 1
        fi
    else
        echo "  ! No integration tests found"
        return 0
    fi
}

# Run all tests
run_all_tests() {
    local fix_id="$1"
    local worktree_path="$2"

    local all_passed=true

    # Run unit tests
    if ! run_unit_tests "${fix_id}" "${worktree_path}"; then
        all_passed=false
    fi

    # Run MCP Inspector
    if ! run_mcp_inspector "${fix_id}" "${worktree_path}"; then
        all_passed=false
    fi

    # Run integration tests
    if ! run_integration_tests "${fix_id}" "${worktree_path}"; then
        all_passed=false
    fi

    if [[ "$all_passed" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# Main execution
main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi

    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
    esac

    local fix_id="$1"

    # Load worktree configuration
    WORKTREE_BASE_DIR=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['worktree_base_dir'])")
    local worktree_path="${WORKTREE_BASE_DIR}/${fix_id}"

    if [[ ! -d "$worktree_path" ]]; then
        echo "ERROR: Worktree not found: ${worktree_path}"
        exit 1
    fi

    echo "========================================="
    echo "Test Runner for ${fix_id}"
    echo "Worktree: ${worktree_path}"
    echo "========================================="
    echo ""

    # Log test start
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | TEST_START | ${fix_id}" >> "${LOGS_DIR}/test-runner.log"

    # Run all tests
    if run_all_tests "${fix_id}" "${worktree_path}"; then
        echo ""
        echo "✅ All tests passed for ${fix_id}"

        # Log test success
        echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | TEST_PASS | ${fix_id}" >> "${LOGS_DIR}/test-runner.log"

        exit 0
    else
        echo ""
        echo "❌ Some tests failed for ${fix_id}"

        # Log test failure
        echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | TEST_FAIL | ${fix_id}" >> "${LOGS_DIR}/test-runner.log"

        exit 1
    fi
}

main "$@"
