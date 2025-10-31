#!/usr/bin/env bash
# MCP Migration Orchestrator
# Coordinates parallel execution of all fixes using git worktrees

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../config"
LOGS_DIR="${SCRIPT_DIR}/../logs"

# Trap handler for cleanup on exit
cleanup_on_exit() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        echo ""
        echo "[ERROR] Orchestrator exited with code ${exit_code}"
        echo "[ERROR] Check logs at: ${LOGS_DIR}/orchestrator.log"
        echo "[ERROR] For status: ${SCRIPT_DIR}/status.sh"
        echo "[ERROR] To rollback: ${SCRIPT_DIR}/rollback.sh"
    fi
}

trap cleanup_on_exit EXIT

# Configuration
DRY_RUN=false
SELECTED_FIXES=""
DEBUG=false
FAILURE_THRESHOLD=50  # Rollback if > 50% of fixes fail
AUTO_ROLLBACK=false  # Set to true to enable automatic rollback on threshold

# Usage information
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Orchestrates parallel execution of MCP migration fixes using git worktrees.

Options:
    --dry-run                     Show execution plan without making changes
    --fixes "fix-1,fix-2"         Execute only specific fixes (comma-separated)
    --debug                       Enable verbose logging
    --failure-threshold PERCENT   Rollback if failure rate exceeds threshold (default: 50)
    --auto-rollback               Enable automatic rollback on failure threshold
    -h, --help                    Show this help message

Examples:
    # Execute all fixes
    $(basename "$0")

    # Dry run to see execution plan
    $(basename "$0") --dry-run

    # Execute only high-priority fixes
    $(basename "$0") --fixes "fix-1-service-prefixes,fix-2-tool-annotations"

    # Debug mode with verbose output
    $(basename "$0") --debug

    # Enable auto-rollback with 30% failure threshold
    $(basename "$0") --auto-rollback --failure-threshold 30
EOF
}

# Logging functions
log_info() {
    echo "[INFO] $*"
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | INFO | $*" >> "${LOGS_DIR}/orchestrator.log"
}

log_error() {
    echo "[ERROR] $*" >&2
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | ERROR | $*" >> "${LOGS_DIR}/orchestrator.log"
}

log_debug() {
    if [[ "$DEBUG" == "true" ]]; then
        echo "[DEBUG] $*"
        echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | DEBUG | $*" >> "${LOGS_DIR}/orchestrator.log"
    fi
}

# Create checkpoint tag for rollback
create_checkpoint() {
    local checkpoint_tag="mcp-migration-checkpoint-$(date -u +%Y%m%d-%H%M%S)"

    log_info "Creating checkpoint tag: ${checkpoint_tag}"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create tag: ${checkpoint_tag}"
        return 0
    fi

    if git tag "${checkpoint_tag}"; then
        log_info "✓ Checkpoint created: ${checkpoint_tag}"
        echo "${checkpoint_tag}" > "${LOGS_DIR}/checkpoint-tag.txt"
    else
        log_error "Failed to create checkpoint tag"
        return 1
    fi
}

# Load execution order from dependency graph
load_execution_order() {
    local config_file="${CONFIG_DIR}/dependency-graph.yaml"
    local selected="${SELECTED_FIXES}"

    python3 - "$config_file" "$selected" <<'EOF'
import sys
import yaml
import json

config_file = sys.argv[1]
selected_fixes = sys.argv[2]

with open(config_file) as f:
    graph = yaml.safe_load(f)

execution_order = graph["execution_order"]

# Filter by selected fixes if specified
if selected_fixes:
    selected = set(selected_fixes.split(","))
    filtered_order = []
    for wave in execution_order:
        filtered_wave = [fix for fix in wave if fix in selected]
        if filtered_wave:
            filtered_order.append(filtered_wave)
    execution_order = filtered_order

print(json.dumps(execution_order))
EOF
}

# Execute a wave of fixes in parallel
execute_wave() {
    local wave_number="$1"
    shift
    local fixes=("$@")

    log_info "Executing Wave ${wave_number} with ${#fixes[@]} fixes..."

    local pids=()
    local fix_results=()

    for fix_id in "${fixes[@]}"; do
        log_info "  Starting: ${fix_id}"

        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "  [DRY RUN] Would execute: ${fix_id}"
            continue
        fi

        # Execute fix in background
        (
            set -euo pipefail

            local fix_log="${LOGS_DIR}/worktree-${fix_id}.log"

            {
                echo "=== Starting execution: ${fix_id} ==="
                echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
                echo ""

                # Create worktree
                "${SCRIPT_DIR}/worktree-manager.sh" create "${fix_id}"

                # Execute fix
                "${SCRIPT_DIR}/fix-executor.sh" "${fix_id}"

                # Run tests
                "${SCRIPT_DIR}/test-runner.sh" "${fix_id}"

                # Create PR
                "${SCRIPT_DIR}/pr-automation.sh" create "${fix_id}"

                echo ""
                echo "=== Completed: ${fix_id} ==="
                echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

            } >> "${fix_log}" 2>&1

            exit_code=$?

            if [[ $exit_code -eq 0 ]]; then
                echo "SUCCESS" > "${LOGS_DIR}/${fix_id}.result"
            else
                echo "FAILED" > "${LOGS_DIR}/${fix_id}.result"
                log_error "Fix ${fix_id} failed with exit code ${exit_code}"
            fi

            exit $exit_code
        ) &

        pids+=($!)
    done

    # Wait for all fixes in this wave to complete
    local all_success=true

    for pid in "${pids[@]}"; do
        if wait "$pid"; then
            log_debug "Process ${pid} completed successfully"
        else
            log_error "Process ${pid} failed"
            all_success=false
        fi
    done

    if [[ "$all_success" == "true" ]]; then
        log_info "✓ Wave ${wave_number} completed successfully"
        return 0
    else
        log_error "Wave ${wave_number} had failures"
        return 1
    fi
}

# Initialize execution state
initialize_state() {
    log_info "Initializing execution state..."

    if [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    # Create state file
    python3 <<EOF
import json
from datetime import datetime

state = {
    "execution_id": "mcp-migration-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S"),
    "start_time": datetime.utcnow().isoformat() + "Z",
    "status": "in_progress",
    "worktrees": []
}

with open("${LOGS_DIR}/execution-state.json", "w") as f:
    json.dump(state, f, indent=2)

print(f"Execution ID: {state['execution_id']}")
EOF
}

# Generate summary report
generate_summary() {
    local total_fixes="$1"
    local successful_fixes="$2"
    local failed_fixes="$3"

    log_info "Generating summary report..."

    cat > "${LOGS_DIR}/summary-report.md" <<EOF
# MCP Migration Summary Report

**Execution ID**: $(cat "${LOGS_DIR}/execution-state.json" | python3 -c "import sys, json; print(json.load(sys.stdin)['execution_id'])")
**Start Time**: $(cat "${LOGS_DIR}/execution-state.json" | python3 -c "import sys, json; print(json.load(sys.stdin)['start_time'])")
**End Time**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Results

- **Total Fixes**: ${total_fixes}
- **Successful**: ${successful_fixes}
- **Failed**: ${failed_fixes}

## Fix Status

EOF

    # Append individual fix results
    for result_file in "${LOGS_DIR}"/*.result; do
        if [[ -f "$result_file" ]]; then
            local fix_id
            fix_id=$(basename "$result_file" .result)
            local status
            status=$(cat "$result_file")

            if [[ "$status" == "SUCCESS" ]]; then
                echo "- ✅ ${fix_id}: SUCCESS" >> "${LOGS_DIR}/summary-report.md"
            else
                echo "- ❌ ${fix_id}: FAILED" >> "${LOGS_DIR}/summary-report.md"
            fi
        fi
    done

    cat >> "${LOGS_DIR}/summary-report.md" <<EOF

## Logs

- Orchestrator log: \`${LOGS_DIR}/orchestrator.log\`
- Individual worktree logs: \`${LOGS_DIR}/worktree-*.log\`
- Execution state: \`${LOGS_DIR}/execution-state.json\`

## Next Steps

EOF

    if [[ "$failed_fixes" -eq 0 ]]; then
        cat >> "${LOGS_DIR}/summary-report.md" <<EOF
✅ **All fixes completed successfully!**

1. Review PRs created: \`gh pr list --label mcp-migration\`
2. Wait for CI checks to pass
3. PRs will auto-merge after CI passes
4. Verify MCP compliance: \`npx @modelcontextprotocol/inspector mcp_stdio_server.py\`
EOF
    else
        cat >> "${LOGS_DIR}/summary-report.md" <<EOF
⚠️ **Some fixes failed. Review and fix issues:**

1. Check failed worktree logs in \`${LOGS_DIR}/\`
2. Fix issues manually in failed worktrees
3. Re-run tests: \`${SCRIPT_DIR}/test-runner.sh <fix_id>\`
4. Create PRs manually: \`${SCRIPT_DIR}/pr-automation.sh create <fix_id>\`
5. Or rollback: \`${SCRIPT_DIR}/rollback.sh\`
EOF
    fi

    log_info "✓ Summary report generated: ${LOGS_DIR}/summary-report.md"

    # Display summary
    cat "${LOGS_DIR}/summary-report.md"
}

# Check failure threshold and trigger rollback if needed
check_failure_threshold() {
    local total_fixes="$1"
    local failed_fixes="$2"

    if [[ $total_fixes -eq 0 ]]; then
        return 0
    fi

    local failure_rate=$(( (failed_fixes * 100) / total_fixes ))

    log_info "Failure rate: ${failure_rate}% (${failed_fixes}/${total_fixes})"
    log_info "Failure threshold: ${FAILURE_THRESHOLD}%"

    if [[ $failure_rate -gt $FAILURE_THRESHOLD ]]; then
        log_error "⚠️  Failure rate (${failure_rate}%) exceeds threshold (${FAILURE_THRESHOLD}%)"

        if [[ "$AUTO_ROLLBACK" == "true" ]]; then
            log_error "🔄 Triggering automatic rollback..."
            echo ""

            # Call rollback script
            if "${SCRIPT_DIR}/rollback.sh" --force; then
                log_info "✓ Rollback completed successfully"
                return 1
            else
                log_error "✗ Rollback failed"
                log_error "Manual intervention required"
                return 1
            fi
        else
            log_error ""
            log_error "Failure threshold exceeded but auto-rollback is disabled."
            log_error "To rollback manually, run:"
            log_error "  ${SCRIPT_DIR}/rollback.sh"
            log_error ""
            log_error "To enable auto-rollback, use --auto-rollback flag"
            return 1
        fi
    fi

    return 0
}

# Main orchestration logic
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --fixes)
                SELECTED_FIXES="$2"
                shift 2
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --failure-threshold)
                FAILURE_THRESHOLD="$2"
                shift 2
                ;;
            --auto-rollback)
                AUTO_ROLLBACK=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo "ERROR: Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    log_info "========================================="
    log_info "MCP Migration Orchestrator Starting"
    log_info "========================================="

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN MODE - No changes will be made"
    fi

    # Validate configuration
    log_info "Validating configuration..."
    if ! "${SCRIPT_DIR}/validate-config.sh"; then
        log_error "Configuration validation failed"
        exit 1
    fi

    # Create checkpoint
    create_checkpoint

    # Initialize state
    initialize_state

    # Load execution order
    log_info "Loading execution order..."
    local execution_order
    execution_order=$(load_execution_order)

    log_debug "Execution order: ${execution_order}"

    # Parse execution waves
    local wave_count
    wave_count=$(echo "$execution_order" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data) if data else 0)")

    log_info "Execution plan: ${wave_count} waves"

    # Display execution plan
    if [[ "$wave_count" -gt 0 ]]; then
        python3 - "$execution_order" <<'EOF'
import sys
import json

execution_order = json.loads(sys.argv[1])

for i, wave in enumerate(execution_order, 1):
    print(f"Wave {i}: {', '.join(wave)}")
EOF
    else
        log_error "No fixes to execute"
        exit 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info ""
        log_info "DRY RUN complete. Use without --dry-run to execute."
        exit 0
    fi

    # Execute waves sequentially (fixes within each wave run in parallel)
    local wave_number=1
    local total_fixes=0
    local successful_fixes=0
    local failed_fixes=0

    while [[ $wave_number -le $wave_count ]]; do
        log_info ""
        log_info "Starting Wave ${wave_number}..."

        # Extract fixes for this wave
        local fixes_json
        fixes_json=$(echo "$execution_order" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin)[${wave_number} - 1]))")

        # Convert JSON array to bash array (compatible with bash 3.2+)
        local fixes=()
        while IFS= read -r fix; do
            fixes+=("$fix")
        done < <(echo "$fixes_json" | python3 -c "import sys, json; print('\n'.join(json.load(sys.stdin)))")

        total_fixes=$((total_fixes + ${#fixes[@]}))

        # Execute wave
        if execute_wave "$wave_number" "${fixes[@]}"; then
            successful_fixes=$((successful_fixes + ${#fixes[@]}))
            log_info "✓ Wave ${wave_number} successful"
        else
            # Count individual successes and failures
            for fix_id in "${fixes[@]}"; do
                if [[ -f "${LOGS_DIR}/${fix_id}.result" ]]; then
                    if grep -q "SUCCESS" "${LOGS_DIR}/${fix_id}.result"; then
                        successful_fixes=$((successful_fixes + 1))
                    else
                        failed_fixes=$((failed_fixes + 1))
                    fi
                else
                    failed_fixes=$((failed_fixes + 1))
                fi
            done

            log_error "Wave ${wave_number} had failures, but continuing..."
        fi

        wave_number=$((wave_number + 1))
    done

    log_info ""
    log_info "========================================="
    log_info "Migration Execution Complete"
    log_info "========================================="

    # Generate summary
    generate_summary "$total_fixes" "$successful_fixes" "$failed_fixes"

    # Check failure threshold and trigger rollback if needed
    if ! check_failure_threshold "$total_fixes" "$failed_fixes"; then
        log_error "Execution aborted due to failure threshold"
        exit 2  # Exit code 2 indicates rollback was triggered
    fi

    # Exit with appropriate code
    if [[ "$failed_fixes" -eq 0 ]]; then
        log_info "✅ All fixes completed successfully!"
        exit 0
    else
        log_error "❌ ${failed_fixes} fix(es) failed"
        log_error "Failure threshold not exceeded (${FAILURE_THRESHOLD}%), continuing..."
        exit 1
    fi
}

main "$@"
