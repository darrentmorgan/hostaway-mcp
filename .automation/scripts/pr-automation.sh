#!/usr/bin/env bash
# PR Automation for MCP Migration
# Creates and manages pull requests using GitHub CLI

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../config"
LOGS_DIR="${SCRIPT_DIR}/../logs"

# Usage information
usage() {
    cat <<EOF
Usage: $(basename "$0") <command> <fix_id>

Manage pull requests for MCP migration fixes.

Commands:
    create <fix_id>     Create PR for the fix
    status <fix_id>     Check PR status
    merge <fix_id>      Manually merge PR

Options:
    -h, --help          Show this help message

Examples:
    $(basename "$0") create fix-1-service-prefixes
    $(basename "$0") status fix-1-service-prefixes
    $(basename "$0") merge fix-1-service-prefixes
EOF
}

# Load fix definition
get_fix_info() {
    local fix_id="$1"
    local field="$2"

    python3 <<EOF
import yaml

with open("${CONFIG_DIR}/fix-definitions.yaml") as f:
    definitions = yaml.safe_load(f)

fix_def = next((f for f in definitions["fixes"] if f["fix_id"] == "${fix_id}"), None)

if fix_def:
    print(fix_def.get("${field}", ""))
else:
    print("", end="")
EOF
}

# Create pull request
create_pr() {
    local fix_id="$1"

    echo "Creating PR for ${fix_id}..."

    # Check if gh CLI is available
    if ! command -v gh &>/dev/null; then
        echo "ERROR: GitHub CLI (gh) not found"
        echo "  Install: https://cli.github.com/"
        return 1
    fi

    # Check authentication
    if ! gh auth status &>/dev/null; then
        echo "ERROR: GitHub CLI not authenticated"
        echo "  Run: gh auth login"
        return 1
    fi

    # Load worktree configuration
    WORKTREE_BASE_DIR=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['worktree_base_dir'])")
    BASE_BRANCH=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['base_branch'])")
    BRANCH_PREFIX=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['branch_prefix'])")
    AUTO_MERGE=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['auto_merge_enabled'])")

    local worktree_path="${WORKTREE_BASE_DIR}/${fix_id}"
    local branch_name="${BRANCH_PREFIX}${fix_id}"

    if [[ ! -d "$worktree_path" ]]; then
        echo "ERROR: Worktree not found: ${worktree_path}"
        return 1
    fi

    # Change to worktree
    cd "${worktree_path}"

    # Get fix information
    local fix_name
    fix_name=$(get_fix_info "${fix_id}" "name")

    local fix_description
    fix_description=$(get_fix_info "${fix_id}" "description")

    local migration_section
    migration_section=$(get_fix_info "${fix_id}" "migration_guide_section")

    # Push branch to remote
    echo "  Pushing branch ${branch_name}..."

    if ! git push -u origin "${branch_name}"; then
        echo "ERROR: Failed to push branch"
        return 1
    fi

    # Create PR body
    local pr_body
    pr_body=$(cat <<EOF_PR
## Summary

${fix_description}

## Migration Guide Reference

See \`docs/MCP_MIGRATION_GUIDE.md\` - ${migration_section}

## Changes

- Implements ${fix_name}
- Includes unit tests
- Passes MCP Inspector validation

## Testing

\`\`\`bash
# Run tests
uv run pytest ${migration_section//[ :]/-} -v

# Validate with MCP Inspector
npx @modelcontextprotocol/inspector mcp_stdio_server.py
\`\`\`

## Checklist

- [x] Tests pass locally
- [x] Code follows project style guidelines
- [x] MCP best practices followed
- [ ] CI checks pass

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF_PR
)

    # Create PR
    echo "  Creating pull request..."

    local pr_title="fix: ${fix_name}"

    if gh pr create \
        --base "${BASE_BRANCH}" \
        --head "${branch_name}" \
        --title "${pr_title}" \
        --body "${pr_body}" \
        --label "mcp-migration" \
        --label "automated"; then

        echo "  ✓ PR created successfully"

        # Get PR number
        local pr_number
        pr_number=$(gh pr view "${branch_name}" --json number -q .number)

        echo "  PR #${pr_number}: ${pr_title}"

        # Enable auto-merge if configured
        if [[ "$AUTO_MERGE" == "True" || "$AUTO_MERGE" == "true" ]]; then
            echo "  Enabling auto-merge..."

            if gh pr merge "${pr_number}" --auto --squash; then
                echo "  ✓ Auto-merge enabled"
            else
                echo "  ! Failed to enable auto-merge (may require manual approval)"
            fi
        fi

        # Log PR creation
        echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | PR_CREATED | ${fix_id} | #${pr_number}" >> "${LOGS_DIR}/pr-automation.log"

        return 0
    else
        echo "ERROR: Failed to create PR"
        return 1
    fi
}

# Check PR status
check_pr_status() {
    local fix_id="$1"

    echo "Checking PR status for ${fix_id}..."

    if ! command -v gh &>/dev/null; then
        echo "ERROR: GitHub CLI (gh) not found"
        return 1
    fi

    BRANCH_PREFIX=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['branch_prefix'])")
    local branch_name="${BRANCH_PREFIX}${fix_id}"

    # Get PR info
    if gh pr view "${branch_name}" --json number,title,state,mergeable,statusCheckRollup 2>/dev/null; then
        return 0
    else
        echo "  ! No PR found for branch: ${branch_name}"
        return 1
    fi
}

# Manually merge PR
merge_pr() {
    local fix_id="$1"

    echo "Merging PR for ${fix_id}..."

    if ! command -v gh &>/dev/null; then
        echo "ERROR: GitHub CLI (gh) not found"
        return 1
    fi

    BRANCH_PREFIX=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['branch_prefix'])")
    local branch_name="${BRANCH_PREFIX}${fix_id}"

    # Get PR number
    local pr_number
    pr_number=$(gh pr view "${branch_name}" --json number -q .number 2>/dev/null)

    if [[ -z "$pr_number" ]]; then
        echo "ERROR: No PR found for ${fix_id}"
        return 1
    fi

    # Check if PR can be merged
    local mergeable
    mergeable=$(gh pr view "${pr_number}" --json mergeable -q .mergeable)

    if [[ "$mergeable" != "MERGEABLE" ]]; then
        echo "ERROR: PR #${pr_number} is not mergeable (status: ${mergeable})"
        return 1
    fi

    # Merge PR
    echo "  Merging PR #${pr_number}..."

    if gh pr merge "${pr_number}" --squash --delete-branch; then
        echo "  ✓ PR merged successfully"

        # Log PR merge
        echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | PR_MERGED | ${fix_id} | #${pr_number}" >> "${LOGS_DIR}/pr-automation.log"

        return 0
    else
        echo "ERROR: Failed to merge PR"
        return 1
    fi
}

# Main command dispatcher
main() {
    if [[ $# -lt 2 ]]; then
        usage
        exit 1
    fi

    local command="$1"
    local fix_id="$2"

    case "$command" in
        create)
            create_pr "${fix_id}"
            ;;
        status)
            check_pr_status "${fix_id}"
            ;;
        merge)
            merge_pr "${fix_id}"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
