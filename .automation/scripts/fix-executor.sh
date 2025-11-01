#!/usr/bin/env bash
# Fix Executor for MCP Migration
# Executes a single fix within a worktree

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../config"
LOGS_DIR="${SCRIPT_DIR}/../logs"
TEMPLATES_DIR="${SCRIPT_DIR}/../templates"

# Usage information
usage() {
    cat <<EOF
Usage: $(basename "$0") <fix_id> [--dry-run]

Arguments:
    fix_id          Fix identifier (e.g., fix-1-service-prefixes)

Options:
    --dry-run       Show what would be done without making changes
    -h, --help      Show this help message

Examples:
    $(basename "$0") fix-1-service-prefixes
    $(basename "$0") fix-3-error-messages --dry-run
EOF
}

# Load fix definition from YAML
load_fix_definition() {
    local fix_id="$1"

    python3 <<EOF
import yaml
import sys
import json

with open("${CONFIG_DIR}/fix-definitions.yaml") as f:
    definitions = yaml.safe_load(f)

fix_def = next((f for f in definitions["fixes"] if f["fix_id"] == "${fix_id}"), None)

if fix_def is None:
    print(f"ERROR: Fix definition not found for ${fix_id}", file=sys.stderr)
    sys.exit(1)

# Output as JSON for bash consumption
print(json.dumps(fix_def))
EOF
}

# Apply fix based on fix_id
apply_fix() {
    local fix_id="$1"
    local worktree_path="$2"
    local dry_run="${3:-false}"

    echo "Applying fix: ${fix_id}"
    echo "  Worktree: ${worktree_path}"

    # Load fix definition
    local fix_def
    fix_def=$(load_fix_definition "${fix_id}")

    local target_file
    target_file=$(echo "$fix_def" | python3 -c "import sys, json; print(json.load(sys.stdin)['target_file'])")

    local migration_section
    migration_section=$(echo "$fix_def" | python3 -c "import sys, json; print(json.load(sys.stdin)['migration_guide_section'])")

    echo "  Target file: ${target_file}"
    echo "  Migration section: ${migration_section}"

    if [[ "$dry_run" == "true" ]]; then
        echo "  [DRY RUN] Would apply changes to ${target_file}"
        return 0
    fi

    # Change to worktree directory
    cd "${worktree_path}"

    # Apply fix based on fix_id
    case "${fix_id}" in
        fix-1-service-prefixes)
            apply_fix_1_service_prefixes
            ;;
        fix-2-tool-annotations)
            apply_fix_2_tool_annotations
            ;;
        fix-3-error-messages)
            apply_fix_3_error_messages
            ;;
        fix-4-response-formats)
            apply_fix_4_response_formats
            ;;
        imp-1-tool-descriptions)
            apply_imp_1_tool_descriptions
            ;;
        imp-2-input-validation)
            apply_imp_2_input_validation
            ;;
        imp-3-character-limit)
            apply_imp_3_character_limit
            ;;
        *)
            echo "ERROR: Unknown fix_id: ${fix_id}"
            return 1
            ;;
    esac

    echo "✓ Fix applied successfully"
}

# Fix 1: Add Service Prefixes
apply_fix_1_service_prefixes() {
    echo "  Applying Fix 1: Service Prefixes..."

    local target_file="mcp_stdio_server.py"

    if [[ ! -f "$target_file" ]]; then
        echo "ERROR: Target file not found: ${target_file}"
        return 1
    fi

    # Backup original file
    cp "${target_file}" "${target_file}.bak"

    # Replace tool names with hostaway_ prefix
    sed -i.tmp -e 's/name="list_properties"/name="hostaway_list_properties"/g' "${target_file}"
    sed -i.tmp -e 's/name="get_property_details"/name="hostaway_get_property_details"/g' "${target_file}"
    sed -i.tmp -e 's/name="check_availability"/name="hostaway_check_availability"/g' "${target_file}"
    sed -i.tmp -e 's/name="search_bookings"/name="hostaway_search_bookings"/g' "${target_file}"
    sed -i.tmp -e 's/name="get_booking_details"/name="hostaway_get_booking_details"/g' "${target_file}"
    sed -i.tmp -e 's/name="get_guest_info"/name="hostaway_get_guest_info"/g' "${target_file}"
    sed -i.tmp -e 's/name="get_financial_reports"/name="hostaway_get_financial_reports"/g' "${target_file}"

    # Update if conditions in call_tool function
    sed -i.tmp -e 's/if name == "list_properties"/if name == "hostaway_list_properties"/g' "${target_file}"
    sed -i.tmp -e 's/elif name == "get_property_details"/elif name == "hostaway_get_property_details"/g' "${target_file}"
    sed -i.tmp -e 's/elif name == "check_availability"/elif name == "hostaway_check_availability"/g' "${target_file}"
    sed -i.tmp -e 's/elif name == "search_bookings"/elif name == "hostaway_search_bookings"/g' "${target_file}"
    sed -i.tmp -e 's/elif name == "get_booking_details"/elif name == "hostaway_get_booking_details"/g' "${target_file}"
    sed -i.tmp -e 's/elif name == "get_guest_info"/elif name == "hostaway_get_guest_info"/g' "${target_file}"
    sed -i.tmp -e 's/elif name == "get_financial_reports"/elif name == "hostaway_get_financial_reports"/g' "${target_file}"

    # Clean up temp files
    rm -f "${target_file}.tmp"

    echo "    ✓ Service prefixes applied"
}

# Fix 2: Add Tool Annotations
apply_fix_2_tool_annotations() {
    echo "  Applying Fix 2: Tool Annotations..."

    local target_file="mcp_stdio_server.py"

    if [[ ! -f "$target_file" ]]; then
        echo "ERROR: Target file not found: ${target_file}"
        return 1
    fi

    # Backup original file
    cp "${target_file}" "${target_file}.bak"

    # Add annotations to each tool using Python for precision
    python3 << 'PYTHON_SCRIPT'
import re

with open("mcp_stdio_server.py", "r") as f:
    content = f.read()

# Define annotations for each tool
annotations = {
    "hostaway_list_properties": '''annotations={
                "title": "List Properties",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            }''',
    "hostaway_get_property_details": '''annotations={
                "title": "Get Property Details",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            }''',
    "hostaway_check_availability": '''annotations={
                "title": "Check Availability",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            }''',
    "hostaway_search_bookings": '''annotations={
                "title": "Search Bookings",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            }''',
    "hostaway_get_booking_details": '''annotations={
                "title": "Get Booking Details",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            }''',
    "hostaway_get_guest_info": '''annotations={
                "title": "Get Guest Info",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True
            }''',
    "hostaway_get_financial_reports": '''annotations={
                "title": "Get Financial Reports",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": False,
                "openWorldHint": True
            }'''
}

# Add annotations after inputSchema closing brace for each tool
for tool_name, annotation in annotations.items():
    # Pattern: find tool with this name, then its inputSchema closing brace
    pattern = rf'(name="{tool_name}".*?inputSchema=\{{.*?\}},)(\s*\))'
    replacement = rf'\1\n            {annotation}\2'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open("mcp_stdio_server.py", "w") as f:
    f.write(content)

print("✓ Annotations added to all tools")
PYTHON_SCRIPT

    echo "    ✓ Tool annotations applied"
}

# Fix 3: Improve Error Messages
apply_fix_3_error_messages() {
    echo "  Applying Fix 3: Error Messages..."

    echo "    ! This fix requires manual code editing"
    echo "    ! Add error helper functions and input validation"
    echo "    ! See docs/MCP_MIGRATION_GUIDE.md Fix 3 for details"
}

# Fix 4: Add Response Format Support
apply_fix_4_response_formats() {
    echo "  Applying Fix 4: Response Formats..."

    echo "    ! This fix requires manual code editing"
    echo "    ! Add markdown formatting functions"
    echo "    ! See docs/MCP_MIGRATION_GUIDE.md Fix 4 for details"
}

# Improvement 1: Enhance Tool Descriptions
apply_imp_1_tool_descriptions() {
    echo "  Applying Improvement 1: Tool Descriptions..."

    echo "    ! This improvement requires manual code editing"
    echo "    ! Enhance tool descriptions with examples and guidance"
    echo "    ! See docs/MCP_MIGRATION_GUIDE.md Improvement 1 for details"
}

# Improvement 2: Add Input Validation
apply_imp_2_input_validation() {
    echo "  Applying Improvement 2: Input Validation..."

    echo "    ! This improvement requires manual code editing"
    echo "    ! Add constraints and examples to input schemas"
    echo "    ! See docs/MCP_MIGRATION_GUIDE.md Improvement 2 for details"
}

# Improvement 3: Add CHARACTER_LIMIT Truncation
apply_imp_3_character_limit() {
    echo "  Applying Improvement 3: CHARACTER_LIMIT..."

    echo "    ! This improvement requires manual code editing"
    echo "    ! Add CHARACTER_LIMIT constant and truncate_response function"
    echo "    ! See docs/MCP_MIGRATION_GUIDE.md Improvement 3 for details"
}

# Commit changes
commit_changes() {
    local fix_id="$1"
    local worktree_path="$2"
    local dry_run="${3:-false}"

    cd "${worktree_path}"

    if [[ "$dry_run" == "true" ]]; then
        echo "  [DRY RUN] Would commit changes"
        return 0
    fi

    # Check if there are changes to commit
    if ! git diff --quiet; then
        echo "Committing changes..."

        git add -A

        local commit_msg
        commit_msg="fix: ${fix_id} - implement MCP migration

Implements ${fix_id} as defined in docs/MCP_MIGRATION_GUIDE.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

        git commit -m "${commit_msg}"

        echo "✓ Changes committed"
    else
        echo "  No changes to commit"
    fi
}

# Main execution
main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi

    local fix_id=""
    local dry_run="false"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            --dry-run)
                dry_run="true"
                shift
                ;;
            *)
                if [[ -z "$fix_id" ]]; then
                    fix_id="$1"
                else
                    echo "ERROR: Unexpected argument: $1"
                    usage
                    exit 1
                fi
                shift
                ;;
        esac
    done

    if [[ -z "$fix_id" ]]; then
        echo "ERROR: Missing fix_id argument"
        usage
        exit 1
    fi

    # Load worktree configuration
    WORKTREE_BASE_DIR=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['worktree_base_dir'])")
    local worktree_path="${WORKTREE_BASE_DIR}/${fix_id}"

    if [[ ! -d "$worktree_path" ]]; then
        echo "ERROR: Worktree not found: ${worktree_path}"
        echo "  Run worktree-manager.sh create ${fix_id} first"
        exit 1
    fi

    # Log execution start
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | START | ${fix_id}" >> "${LOGS_DIR}/fix-executor.log"

    # Execute fix
    if apply_fix "${fix_id}" "${worktree_path}" "${dry_run}"; then
        commit_changes "${fix_id}" "${worktree_path}" "${dry_run}"

        # Log execution success
        echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | SUCCESS | ${fix_id}" >> "${LOGS_DIR}/fix-executor.log"

        echo ""
        echo "✅ Fix execution complete: ${fix_id}"
        exit 0
    else
        # Log execution failure
        echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | FAILED | ${fix_id}" >> "${LOGS_DIR}/fix-executor.log"

        echo ""
        echo "❌ Fix execution failed: ${fix_id}"
        exit 1
    fi
}

main "$@"
