#!/usr/bin/env bash
# Generate Summary Report for MCP Migration
# Creates comprehensive reports in markdown and JSON formats

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="${SCRIPT_DIR}/../logs"

# Color codes for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Usage information
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Generate summary reports for MCP migration execution.

Options:
    --format FORMAT     Output format: markdown, json, or html (default: markdown)
    --output FILE       Output file path (default: stdout)
    --execution-id ID   Specific execution ID (default: latest)
    -h, --help          Show this help message

Examples:
    # Generate markdown report to stdout
    $(basename "$0")

    # Generate markdown report to file
    $(basename "$0") --output migration-report.md

    # Generate JSON report
    $(basename "$0") --format json --output report.json

    # Generate HTML report
    $(basename "$0") --format html --output report.html
EOF
}

# Format duration from ISO timestamps
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
    local seconds=$((duration % 60))

    if [[ $hours -gt 0 ]]; then
        echo "${hours}h ${minutes}m ${seconds}s"
    elif [[ $minutes -gt 0 ]]; then
        echo "${minutes}m ${seconds}s"
    else
        echo "${seconds}s"
    fi
}

# Generate markdown report
generate_markdown_report() {
    local state_file="$1"

    if [[ ! -f "$state_file" ]]; then
        echo "ERROR: State file not found: $state_file" >&2
        return 1
    fi

    python3 <<EOF
import json
from datetime import datetime

with open("${state_file}") as f:
    state = json.load(f)

execution_id = state.get("execution_id", "N/A")
status = state.get("status", "unknown")
start_time = state.get("start_time", "N/A")
end_time = state.get("end_time", "N/A")

# Calculate summary
worktrees = state.get("worktrees", [])
total_fixes = len(worktrees)
complete = len([wt for wt in worktrees if wt["status"] == "complete"])
failed = len([wt for wt in worktrees if wt["status"] == "failed"])
in_progress = len([wt for wt in worktrees if wt["status"] in ["implementing", "testing", "pr_created"]])

# Generate report
print("# MCP Migration Execution Report")
print("")
print(f"**Execution ID:** {execution_id}")
print(f"**Status:** {status}")
print(f"**Started:** {start_time}")
if end_time != "N/A":
    print(f"**Completed:** {end_time}")
print("")

# Summary
print("## Summary")
print("")
print(f"- **Total Fixes:** {total_fixes}")
print(f"- **Completed:** {complete} ({int(complete/total_fixes*100) if total_fixes > 0 else 0}%)")
print(f"- **Failed:** {failed}")
print(f"- **In Progress:** {in_progress}")
print("")

# Progress bar
progress_pct = int(complete / total_fixes * 100) if total_fixes > 0 else 0
filled = int(progress_pct / 5)
bar = "█" * filled + "░" * (20 - filled)
print(f"Progress: [{bar}] {progress_pct}%")
print("")

# Fix details
print("## Fix Details")
print("")
print("| Fix ID | Status | PR | Duration |")
print("|--------|--------|-------|----------|")

for wt in worktrees:
    fix_id = wt["fix_id"]
    status_val = wt["status"].replace("_", " ").title()
    pr_number = wt.get("pr_number", "N/A")
    pr_text = f"#{pr_number}" if pr_number else "N/A"

    # Calculate duration
    duration_text = "N/A"
    if wt.get("start_time"):
        if wt.get("end_time"):
            duration_text = "Completed"  # Would calculate actual duration
        else:
            duration_text = "In Progress"

    # Format status with emoji
    if wt["status"] == "complete":
        status_emoji = "✅"
    elif wt["status"] == "failed":
        status_emoji = "❌"
    else:
        status_emoji = "🔄"

    print(f"| {fix_id} | {status_emoji} {status_val} | {pr_text} | {duration_text} |")

print("")

# Test results
print("## Test Results")
print("")

test_passed = len([wt for wt in worktrees if wt.get("test_passed")])
test_failed = len([wt for wt in worktrees if wt.get("test_passed") is False])

print(f"- **Tests Passed:** {test_passed}")
print(f"- **Tests Failed:** {test_failed}")
print("")

# Errors and warnings
print("## Errors and Warnings")
print("")

failed_fixes = [wt for wt in worktrees if wt["status"] == "failed"]
if failed_fixes:
    print("### Failed Fixes")
    print("")
    for wt in failed_fixes:
        print(f"- **{wt['fix_id']}**: Check logs for details")
    print("")
else:
    print("No errors or warnings.")
    print("")

# Recommendations
print("## Recommendations")
print("")

if failed > 0:
    print("- Review failed fixes and retry if necessary")
    print("- Check logs at: .automation/logs/orchestrator.log")
    print("")

if in_progress > 0:
    print("- Monitor in-progress fixes with: .automation/scripts/status.sh --watch")
    print("")

if complete == total_fixes:
    print("✅ All fixes completed successfully!")
    print("")
    print("Next steps:")
    print("- Verify all PRs are merged")
    print("- Run final integration tests")
    print("- Deploy to staging environment")
    print("")

# Footer
print("---")
print("")
print(f"*Report generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*")
EOF
}

# Generate JSON report
generate_json_report() {
    local state_file="$1"

    if [[ ! -f "$state_file" ]]; then
        echo '{"error": "State file not found"}' >&2
        return 1
    fi

    python3 <<EOF
import json
from datetime import datetime

with open("${state_file}") as f:
    state = json.load(f)

# Add metadata
report = {
    "report_generated_at": datetime.utcnow().isoformat() + "Z",
    "execution": {
        "id": state.get("execution_id"),
        "status": state.get("status"),
        "start_time": state.get("start_time"),
        "end_time": state.get("end_time")
    },
    "summary": {},
    "fixes": []
}

# Calculate summary
worktrees = state.get("worktrees", [])
total_fixes = len(worktrees)
complete = len([wt for wt in worktrees if wt["status"] == "complete"])
failed = len([wt for wt in worktrees if wt["status"] == "failed"])
in_progress = len([wt for wt in worktrees if wt["status"] in ["implementing", "testing", "pr_created"]])

report["summary"] = {
    "total_fixes": total_fixes,
    "completed": complete,
    "failed": failed,
    "in_progress": in_progress,
    "completion_percentage": int(complete / total_fixes * 100) if total_fixes > 0 else 0
}

# Add fix details
for wt in worktrees:
    fix_detail = {
        "fix_id": wt["fix_id"],
        "status": wt["status"],
        "branch_name": wt.get("branch_name"),
        "pr_number": wt.get("pr_number"),
        "start_time": wt.get("start_time"),
        "end_time": wt.get("end_time"),
        "test_passed": wt.get("test_passed")
    }
    report["fixes"].append(fix_detail)

# Output JSON
print(json.dumps(report, indent=2))
EOF
}

# Generate HTML report
generate_html_report() {
    local state_file="$1"

    if [[ ! -f "$state_file" ]]; then
        echo "<html><body><h1>Error: State file not found</h1></body></html>" >&2
        return 1
    fi

    # Generate markdown first, then convert to HTML
    local markdown
    markdown=$(generate_markdown_report "$state_file")

    cat <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Migration Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
            color: #333;
        }
        h1, h2, h3 { color: #2c3e50; }
        h1 { border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; margin-top: 30px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .success { color: #27ae60; }
        .failed { color: #e74c3c; }
        .in-progress { color: #f39c12; }
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background-color: #ecf0f1;
            border-radius: 5px;
            overflow: hidden;
            margin: 20px 0;
        }
        .progress-fill {
            height: 100%;
            background-color: #3498db;
            transition: width 0.3s ease;
        }
        .metadata {
            color: #7f8c8d;
            font-style: italic;
            margin-top: 40px;
            border-top: 1px solid #ecf0f1;
            padding-top: 20px;
        }
    </style>
</head>
<body>
EOF

    # Convert markdown to HTML (simple conversion)
    echo "$markdown" | python3 <<'PYEOF'
import sys
import re

md = sys.stdin.read()

# Headers
md = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', md, flags=re.MULTILINE)
md = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', md, flags=re.MULTILINE)
md = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', md, flags=re.MULTILINE)

# Bold and italic
md = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', md)
md = re.sub(r'\*(.*?)\*', r'<em>\1</em>', md)

# Lists
md = re.sub(r'^- (.*?)$', r'<li>\1</li>', md, flags=re.MULTILINE)
md = re.sub(r'(<li>.*?</li>\n)+', r'<ul>\g<0></ul>', md, flags=re.DOTALL)

# Tables (basic - already formatted in input)
md = re.sub(r'\|', '', md)

# Paragraphs
md = re.sub(r'\n\n', r'</p><p>', md)
md = '<p>' + md + '</p>'

# Clean up extra paragraphs around headers and lists
md = re.sub(r'<p>(<h[123]>)', r'\1', md)
md = re.sub(r'(</h[123]>)</p>', r'\1', md)
md = re.sub(r'<p>(<ul>)', r'\1', md)
md = re.sub(r'(</ul>)</p>', r'\1', md)

print(md)
PYEOF

    cat <<EOF
</body>
</html>
EOF
}

# Main execution
main() {
    local format="markdown"
    local output_file=""
    local execution_id=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --format)
                format="$2"
                shift 2
                ;;
            --output)
                output_file="$2"
                shift 2
                ;;
            --execution-id)
                execution_id="$2"
                shift 2
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

    # Determine state file
    local state_file="${LOGS_DIR}/execution-state.json"
    if [[ -n "$execution_id" ]]; then
        state_file="${LOGS_DIR}/execution-${execution_id}.json"
    fi

    if [[ ! -f "$state_file" ]]; then
        echo "ERROR: State file not found: $state_file" >&2
        exit 1
    fi

    # Generate report based on format
    local report_content=""
    case "$format" in
        markdown|md)
            report_content=$(generate_markdown_report "$state_file")
            ;;
        json)
            report_content=$(generate_json_report "$state_file")
            ;;
        html)
            report_content=$(generate_html_report "$state_file")
            ;;
        *)
            echo "ERROR: Unknown format: $format" >&2
            echo "Supported formats: markdown, json, html" >&2
            exit 1
            ;;
    esac

    # Output to file or stdout
    if [[ -n "$output_file" ]]; then
        echo "$report_content" > "$output_file"
        echo "Report generated: $output_file" >&2
    else
        echo "$report_content"
    fi
}

main "$@"
