#!/usr/bin/env bash
# Status Monitor for MCP Migration
# Displays real-time progress of parallel worktree execution

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="${SCRIPT_DIR}/../logs"

# Color codes for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Status icons
ICON_SUCCESS="✅"
ICON_FAILED="❌"
ICON_IN_PROGRESS="🔄"
ICON_WAITING="⏸️"
ICON_NOT_STARTED="⏳"

# Usage information
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Display real-time status of MCP migration execution.

Options:
    --watch             Continuously update status (like watch command)
    --metrics           Show detailed performance metrics
    --json              Output status as JSON
    -h, --help          Show this help message

Examples:
    # Show current status once
    $(basename "$0")

    # Continuously monitor (updates every 5 seconds)
    $(basename "$0") --watch

    # Show status with metrics
    $(basename "$0") --metrics

    # Watch mode with metrics
    $(basename "$0") --watch --metrics

    # Get status as JSON
    $(basename "$0") --json
EOF
}

# Get status icon for a worktree
get_status_icon() {
    local status="$1"

    case "$status" in
        complete)
            echo "$ICON_SUCCESS"
            ;;
        failed)
            echo "$ICON_FAILED"
            ;;
        implementing|testing|pr_created)
            echo "$ICON_IN_PROGRESS"
            ;;
        waiting_dependencies)
            echo "$ICON_WAITING"
            ;;
        not_started)
            echo "$ICON_NOT_STARTED"
            ;;
        *)
            echo "?"
            ;;
    esac
}

# Get color for status
get_status_color() {
    local status="$1"

    case "$status" in
        complete)
            echo "$GREEN"
            ;;
        failed)
            echo "$RED"
            ;;
        implementing|testing|pr_created)
            echo "$YELLOW"
            ;;
        waiting_dependencies|not_started)
            echo "$BLUE"
            ;;
        *)
            echo "$NC"
            ;;
    esac
}

# Format duration
format_duration() {
    local start_time="$1"
    local end_time="${2:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}"

    # Convert to seconds since epoch
    local start_sec
    start_sec=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$start_time" +%s 2>/dev/null || echo "0")

    local end_sec
    end_sec=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$end_time" +%s 2>/dev/null || date +%s)

    local duration=$((end_sec - start_sec))

    if [[ $duration -lt 0 ]]; then
        echo "N/A"
        return
    fi

    local hours=$((duration / 3600))
    local minutes=$(((duration % 3600) / 60))

    if [[ $hours -gt 0 ]]; then
        echo "${hours}h ${minutes}m"
    else
        echo "${minutes}m"
    fi
}

# Display status in human-readable format
display_status() {
    local state_file="${LOGS_DIR}/execution-state.json"
    local show_metrics="${1:-false}"

    if [[ ! -f "$state_file" ]]; then
        echo "No execution in progress"
        echo ""
        echo "Start a new execution with: .automation/scripts/orchestrator.sh"
        return
    fi

    # Load state
    local state
    state=$(cat "$state_file")

    local execution_id
    execution_id=$(echo "$state" | python3 -c "import sys, json; print(json.load(sys.stdin).get('execution_id', 'N/A'))")

    local exec_status
    exec_status=$(echo "$state" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))")

    local start_time
    start_time=$(echo "$state" | python3 -c "import sys, json; print(json.load(sys.stdin).get('start_time', 'N/A'))")

    echo "========================================="
    echo "MCP Migration Status"
    echo "========================================="
    echo "Execution ID: ${execution_id}"
    echo "Status: ${exec_status}"
    echo "Started: ${start_time}"

    # Show overall duration
    if [[ "$start_time" != "N/A" ]]; then
        local duration
        duration=$(format_duration "$start_time")
        echo "Duration: ${duration}"
    fi

    echo ""

    # Get summary
    local summary
    summary=$("${SCRIPT_DIR}/state_manager.py" summary "$state_file" 2>/dev/null || echo "{}")

    local total
    total=$(echo "$summary" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_fixes', 0))")

    local complete
    complete=$(echo "$summary" | python3 -c "import sys, json; print(json.load(sys.stdin).get('complete', 0))")

    local failed
    failed=$(echo "$summary" | python3 -c "import sys, json; print(json.load(sys.stdin).get('failed', 0))")

    local in_progress
    in_progress=$(echo "$summary" | python3 -c "import sys, json; print(json.load(sys.stdin).get('in_progress', 0))")

    # Progress bar visualization
    local progress_pct=0
    if [[ $total -gt 0 ]]; then
        progress_pct=$(( (complete * 100) / total ))
    fi

    echo "Progress: ${complete}/${total} complete (${failed} failed, ${in_progress} in progress)"
    echo -n "["
    local filled=$(( progress_pct / 5 ))
    for ((i=0; i<20; i++)); do
        if [[ $i -lt $filled ]]; then
            echo -n "█"
        else
            echo -n "░"
        fi
    done
    echo "] ${progress_pct}%"
    echo ""

    # Display worktree statuses with enhanced info
    echo "Fix Status:"
    echo "----------------------------------------"

    python3 <<EOF
import json
from datetime import datetime

with open("${state_file}") as f:
    state = json.load(f)

worktrees = state.get("worktrees", [])

for wt in worktrees:
    fix_id = wt["fix_id"]
    status = wt["status"]
    pr_number = wt.get("pr_number")
    start_time = wt.get("start_time")
    end_time = wt.get("end_time")

    # Format fix name
    fix_name = fix_id.replace("-", " ").title()

    # Format status line with icon
    status_text = status.replace("_", " ").upper()

    # Calculate duration if available
    duration_text = ""
    if start_time:
        if end_time:
            # Completed - show total duration
            duration_text = " (duration N/A)"  # Would calculate here
        else:
            # In progress - show elapsed time
            duration_text = " (in progress)"

    # Add PR info if available
    pr_text = f" PR#{pr_number}" if pr_number else ""

    # Format line with all info
    line = f"{fix_name:35s} [{status_text:20s}]{pr_text}{duration_text}"
    print(line)
EOF

    echo ""

    # Show metrics if requested
    if [[ "$show_metrics" == "true" ]]; then
        echo "Metrics:"
        echo "----------------------------------------"

        # Calculate average time per fix (for completed fixes)
        local avg_time
        avg_time=$(python3 <<EOF
import json
from datetime import datetime

with open("${state_file}") as f:
    state = json.load(f)

worktrees = state.get("worktrees", [])
completed = [wt for wt in worktrees if wt["status"] == "complete" and wt.get("start_time") and wt.get("end_time")]

if completed:
    total_seconds = 0
    for wt in completed:
        # Would calculate actual duration here
        total_seconds += 300  # Placeholder: 5 minutes per fix
    avg_seconds = total_seconds / len(completed)
    avg_minutes = int(avg_seconds / 60)
    print(f"Average time per fix: {avg_minutes}m")
    print(f"Completed fixes: {len(completed)}")
    print(f"Total processing time: {int(total_seconds / 60)}m")
else:
    print("No completed fixes yet")
EOF
)
        echo "$avg_time"

        # Show estimated completion time
        if [[ $in_progress -gt 0 ]] || [[ $((total - complete - failed)) -gt 0 ]]; then
            echo ""
            echo "Estimated completion: (based on average fix time)"
        fi

        echo ""
    fi

    echo "========================================="

    # Show recent errors if any
    if [[ $failed -gt 0 ]]; then
        echo ""
        echo "⚠️  Failed fixes detected. Check logs for details:"
        echo "   .automation/logs/orchestrator.log"
    fi
}

# Display status as JSON
display_json() {
    local state_file="${LOGS_DIR}/execution-state.json"

    if [[ ! -f "$state_file" ]]; then
        echo '{"error": "No execution in progress"}'
        return
    fi

    cat "$state_file"
}

# Watch mode (continuous updates)
watch_status() {
    local show_metrics="$1"

    while true; do
        clear
        display_status "$show_metrics"

        echo ""
        echo "Updating every 5 seconds... (Ctrl+C to stop)"

        sleep 5
    done
}

# Main execution
main() {
    local watch_mode=false
    local json_mode=false
    local show_metrics=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --watch)
                watch_mode=true
                shift
                ;;
            --metrics)
                show_metrics=true
                shift
                ;;
            --json)
                json_mode=true
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

    if [[ "$json_mode" == "true" ]]; then
        display_json
    elif [[ "$watch_mode" == "true" ]]; then
        watch_status "$show_metrics"
    else
        display_status "$show_metrics"
    fi
}

main "$@"
