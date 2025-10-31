#!/usr/bin/env bash
# Rollback Script for MCP Migration
# Emergency rollback to pre-migration state

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../config"
LOGS_DIR="${SCRIPT_DIR}/../logs"

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Usage information
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Emergency rollback to pre-migration checkpoint.

⚠️  WARNING: This will:
  - Stop all running worktrees
  - Close all open PRs
  - Reset main branch to checkpoint tag
  - Delete all worktrees and branches

Options:
    --force            Skip confirmation prompt
    --fix-id FIX_ID    Rollback specific fix only (selective rollback)
    --dry-run          Show what would be done without making changes
    --create-backup    Create git bundle backup before rollback
    -h, --help         Show this help message

Examples:
    # Full rollback with confirmation
    $(basename "$0")

    # Full rollback without confirmation
    $(basename "$0") --force

    # Rollback specific fix only
    $(basename "$0") --fix-id fix-1-service-prefixes

    # Dry run to see what would happen
    $(basename "$0") --dry-run

    # Create backup before rollback
    $(basename "$0") --create-backup --force
EOF
}

# Confirmation prompt
confirm_rollback() {
    echo -e "${RED}⚠️  WARNING: This will rollback ALL migration changes${NC}"
    echo ""
    echo "This action will:"
    echo "  - Close all PRs"
    echo "  - Delete all worktrees"
    echo "  - Reset to checkpoint tag"
    echo ""
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " -r
    echo ""

    if [[ ! $REPLY =~ ^yes$ ]]; then
        echo "Rollback cancelled"
        exit 0
    fi
}

# Get checkpoint tag
get_checkpoint_tag() {
    local checkpoint_file="${LOGS_DIR}/checkpoint-tag.txt"

    if [[ -f "$checkpoint_file" ]]; then
        cat "$checkpoint_file"
    else
        echo ""
    fi
}

# Stop all running worktrees
stop_worktrees() {
    echo "Stopping all worktrees..."

    # Kill any running fix-executor processes
    pkill -f "fix-executor.sh" 2>/dev/null || true
    pkill -f "test-runner.sh" 2>/dev/null || true

    echo "  ✓ Stopped all worktree processes"
}

# Close all PRs
close_prs() {
    echo "Closing all MCP migration PRs..."

    if ! command -v gh &>/dev/null; then
        echo "  ! GitHub CLI not found, skipping PR closure"
        return 0
    fi

    # Get all PRs with mcp-migration label
    local prs
    prs=$(gh pr list --label mcp-migration --json number -q '.[].number' 2>/dev/null || echo "")

    if [[ -z "$prs" ]]; then
        echo "  ! No PRs found"
        return 0
    fi

    for pr_number in $prs; do
        echo "  Closing PR #${pr_number}..."

        if gh pr close "${pr_number}" --comment "Rollback: Closing due to migration rollback"; then
            echo "    ✓ Closed PR #${pr_number}"
        else
            echo "    ! Failed to close PR #${pr_number}"
        fi
    done
}

# Delete all worktrees
delete_worktrees() {
    echo "Deleting all worktrees..."

    WORKTREE_BASE_DIR=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['worktree_base_dir'])" 2>/dev/null || echo "/tmp/hostaway-mcp-worktrees")

    if [[ -d "$WORKTREE_BASE_DIR" ]]; then
        # Remove each worktree
        for worktree_path in "${WORKTREE_BASE_DIR}"/*; do
            if [[ -d "$worktree_path" ]]; then
                local fix_id
                fix_id=$(basename "$worktree_path")

                echo "  Removing worktree: ${fix_id}..."

                if git worktree remove "$worktree_path" --force 2>/dev/null; then
                    echo "    ✓ Removed ${fix_id}"
                else
                    echo "    ! Failed to remove ${fix_id}"
                fi
            fi
        done

        # Clean up base directory
        rm -rf "${WORKTREE_BASE_DIR}"
    fi

    # Prune worktree references
    git worktree prune

    echo "  ✓ All worktrees deleted"
}

# Delete all migration branches
delete_branches() {
    echo "Deleting migration branches..."

    BRANCH_PREFIX=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['branch_prefix'])" 2>/dev/null || echo "mcp-")

    # Get all local branches with prefix
    local branches
    branches=$(git branch --list "${BRANCH_PREFIX}*" --format='%(refname:short)')

    if [[ -z "$branches" ]]; then
        echo "  ! No branches found"
        return 0
    fi

    for branch in $branches; do
        echo "  Deleting branch: ${branch}..."

        if git branch -D "$branch" 2>/dev/null; then
            echo "    ✓ Deleted ${branch}"
        else
            echo "    ! Failed to delete ${branch}"
        fi
    done

    # Delete remote branches
    echo "  Deleting remote branches..."

    for branch in $branches; do
        if git push origin --delete "$branch" 2>/dev/null; then
            echo "    ✓ Deleted remote ${branch}"
        else
            echo "    ! Failed to delete remote ${branch} (may not exist)"
        fi
    done

    echo "  ✓ All branches deleted"
}

# Reset to checkpoint
reset_to_checkpoint() {
    local checkpoint_tag="$1"

    echo "Resetting to checkpoint: ${checkpoint_tag}..."

    BASE_BRANCH=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['base_branch'])" 2>/dev/null || echo "main")

    # Ensure we're on the base branch
    git checkout "$BASE_BRANCH"

    # Hard reset to checkpoint
    if git reset --hard "$checkpoint_tag"; then
        echo "  ✓ Reset to ${checkpoint_tag}"
    else
        echo "  ✗ Failed to reset to ${checkpoint_tag}"
        return 1
    fi
}

# Clean up logs
clean_logs() {
    echo "Cleaning up logs..."

    if [[ -d "$LOGS_DIR" ]]; then
        # Archive current logs
        local archive_name="rollback-archive-$(date +%Y%m%d-%H%M%S).tar.gz"

        if tar -czf "${LOGS_DIR}/${archive_name}" "${LOGS_DIR}"/*.log "${LOGS_DIR}"/*.json 2>/dev/null; then
            echo "  ✓ Logs archived to ${archive_name}"
        fi

        # Remove log files (keep .gitignore)
        find "$LOGS_DIR" -type f ! -name '.gitignore' ! -name '*.tar.gz' -delete

        echo "  ✓ Logs cleaned"
    fi
}

# Create backup bundle
create_backup() {
    local backup_dir="${LOGS_DIR}/backups"
    mkdir -p "$backup_dir"

    local backup_file="${backup_dir}/pre-rollback-$(date +%Y%m%d-%H%M%S).bundle"

    echo "Creating git bundle backup..."
    echo "  Output: ${backup_file}"

    # Create bundle of all branches
    if git bundle create "$backup_file" --all; then
        echo "  ✓ Backup created successfully"
        echo ""
        echo "  To restore from backup:"
        echo "    git clone ${backup_file} restored-repo"
        return 0
    else
        echo "  ✗ Failed to create backup"
        return 1
    fi
}

# Selective rollback for a single fix
selective_rollback() {
    local fix_id="$1"
    local dry_run="${2:-false}"

    echo "Selective rollback for: ${fix_id}"
    echo ""

    WORKTREE_BASE_DIR=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['worktree_base_dir'])" 2>/dev/null || echo "/tmp/hostaway-mcp-worktrees")
    BRANCH_PREFIX=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['branch_prefix'])" 2>/dev/null || echo "mcp-")

    local worktree_path="${WORKTREE_BASE_DIR}/${fix_id}"
    local branch_name="${BRANCH_PREFIX}${fix_id}"

    # Get PR number from state
    local pr_number=""
    if [[ -f "${LOGS_DIR}/execution-state.json" ]]; then
        pr_number=$(python3 <<EOF
import json
with open("${LOGS_DIR}/execution-state.json") as f:
    state = json.load(f)
worktrees = state.get("worktrees", [])
wt = next((w for w in worktrees if w["fix_id"] == "${fix_id}"), None)
if wt and wt.get("pr_number"):
    print(wt["pr_number"])
EOF
)
    fi

    # Show what will be done
    echo "Actions:"
    echo "  - Close PR #${pr_number:-N/A}"
    echo "  - Delete worktree: ${worktree_path}"
    echo "  - Delete branch: ${branch_name}"
    echo ""

    if [[ "$dry_run" == "true" ]]; then
        echo "[DRY RUN] No changes made"
        return 0
    fi

    # Close PR if exists
    if [[ -n "$pr_number" ]] && command -v gh &>/dev/null; then
        echo "Closing PR #${pr_number}..."
        if gh pr close "${pr_number}" --comment "Rollback: Reverting ${fix_id}"; then
            echo "  ✓ PR closed"
        else
            echo "  ! Failed to close PR"
        fi
    fi

    # Remove worktree
    if [[ -d "$worktree_path" ]]; then
        echo "Removing worktree..."
        if git worktree remove "$worktree_path" --force; then
            echo "  ✓ Worktree removed"
        else
            echo "  ! Failed to remove worktree"
        fi
    fi

    # Delete branch
    if git show-ref --verify --quiet "refs/heads/${branch_name}"; then
        echo "Deleting branch..."
        if git branch -D "$branch_name"; then
            echo "  ✓ Branch deleted"
        else
            echo "  ! Failed to delete branch"
        fi

        # Delete remote branch
        if git push origin --delete "$branch_name" 2>/dev/null; then
            echo "  ✓ Remote branch deleted"
        else
            echo "  ! Remote branch may not exist"
        fi
    fi

    echo ""
    echo "✅ Selective rollback complete for ${fix_id}"
}

# Dry run - show what would be done
dry_run_rollback() {
    local checkpoint_tag="$1"

    echo "========================================="
    echo "DRY RUN - No changes will be made"
    echo "========================================="
    echo ""

    echo "The following actions would be performed:"
    echo ""

    # Show worktrees that would be stopped
    echo "1. Stop running processes:"
    if pgrep -f "fix-executor.sh" &>/dev/null; then
        echo "   - fix-executor.sh processes would be killed"
    else
        echo "   - No running processes"
    fi

    # Show PRs that would be closed
    echo ""
    echo "2. Close PRs:"
    if command -v gh &>/dev/null; then
        local prs
        prs=$(gh pr list --label mcp-migration --json number,title -q '.[] | "\(.number): \(.title)"' 2>/dev/null || echo "")
        if [[ -n "$prs" ]]; then
            echo "$prs" | while read -r line; do
                echo "   - PR #${line}"
            done
        else
            echo "   - No PRs found"
        fi
    else
        echo "   - GitHub CLI not available"
    fi

    # Show worktrees that would be deleted
    echo ""
    echo "3. Delete worktrees:"
    WORKTREE_BASE_DIR=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['worktree_base_dir'])" 2>/dev/null || echo "/tmp/hostaway-mcp-worktrees")
    if [[ -d "$WORKTREE_BASE_DIR" ]]; then
        for worktree_path in "${WORKTREE_BASE_DIR}"/*; do
            if [[ -d "$worktree_path" ]]; then
                echo "   - $(basename "$worktree_path")"
            fi
        done
    else
        echo "   - No worktrees found"
    fi

    # Show branches that would be deleted
    echo ""
    echo "4. Delete branches:"
    BRANCH_PREFIX=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['branch_prefix'])" 2>/dev/null || echo "mcp-")
    local branches
    branches=$(git branch --list "${BRANCH_PREFIX}*" --format='%(refname:short)')
    if [[ -n "$branches" ]]; then
        echo "$branches" | while read -r branch; do
            echo "   - ${branch}"
        done
    else
        echo "   - No branches found"
    fi

    # Show reset that would be performed
    echo ""
    echo "5. Reset to checkpoint:"
    echo "   - Tag: ${checkpoint_tag}"
    echo "   - Current HEAD would be reset to this tag"

    echo ""
    echo "========================================="
    echo "END DRY RUN"
    echo "========================================="
}

# Main rollback execution
main() {
    local force=false
    local fix_id=""
    local dry_run=false
    local create_backup_flag=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force)
                force=true
                shift
                ;;
            --fix-id)
                fix_id="$2"
                shift 2
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --create-backup)
                create_backup_flag=true
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

    echo "========================================="
    echo "MCP Migration Rollback"
    echo "========================================="
    echo ""

    # Handle selective rollback
    if [[ -n "$fix_id" ]]; then
        selective_rollback "$fix_id" "$dry_run"
        exit 0
    fi

    # Get checkpoint tag
    local checkpoint_tag
    checkpoint_tag=$(get_checkpoint_tag)

    if [[ -z "$checkpoint_tag" ]]; then
        echo -e "${RED}ERROR: No checkpoint tag found${NC}"
        echo ""
        echo "Cannot rollback without a checkpoint."
        echo "Check ${LOGS_DIR}/checkpoint-tag.txt"
        exit 1
    fi

    echo "Checkpoint tag: ${checkpoint_tag}"
    echo ""

    # Handle dry run
    if [[ "$dry_run" == "true" ]]; then
        dry_run_rollback "$checkpoint_tag"
        exit 0
    fi

    # Confirmation unless --force
    if [[ "$force" != "true" ]]; then
        confirm_rollback
    fi

    # Create backup if requested
    if [[ "$create_backup_flag" == "true" ]]; then
        create_backup
        echo ""
    fi

    # Execute rollback steps
    stop_worktrees
    echo ""

    close_prs
    echo ""

    delete_worktrees
    echo ""

    delete_branches
    echo ""

    reset_to_checkpoint "$checkpoint_tag"
    echo ""

    clean_logs
    echo ""

    echo "========================================="
    echo -e "${GREEN}✅ Rollback complete${NC}"
    echo "========================================="
    echo ""
    echo "Your repository has been restored to:"
    echo "  Tag: ${checkpoint_tag}"
    echo ""
    echo "Archived logs: ${LOGS_DIR}/rollback-archive-*.tar.gz"

    if [[ "$create_backup_flag" == "true" ]]; then
        echo "Backup bundle: ${LOGS_DIR}/backups/pre-rollback-*.bundle"
    fi
}

main "$@"
