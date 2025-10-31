#!/usr/bin/env bash
# Cleanup Script for MCP Migration
# Removes stale worktrees, old logs, and orphaned branches

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../config"
LOGS_DIR="${SCRIPT_DIR}/../logs"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
KEEP_LAST_N_LOGS=10
DRY_RUN=false

# Usage information
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Clean up stale worktrees, old logs, and orphaned branches.

Options:
    --dry-run           Show what would be cleaned without making changes
    --keep-logs N       Keep last N log runs (default: ${KEEP_LAST_N_LOGS})
    --all               Clean everything (logs, worktrees, branches)
    -h, --help          Show this help message

Examples:
    # Dry run to see what would be cleaned
    $(basename "$0") --dry-run

    # Clean with default settings
    $(basename "$0")

    # Keep last 20 log runs
    $(basename "$0") --keep-logs 20

    # Clean everything
    $(basename "$0") --all
EOF
}

# Clean stale worktrees
clean_worktrees() {
    echo "Cleaning stale worktrees..."

    # Prune worktree references
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  [DRY RUN] Would run: git worktree prune"
    else
        if git worktree prune --verbose; then
            echo "  ✓ Pruned stale worktree references"
        else
            echo "  ! No stale worktrees found"
        fi
    fi

    # Find and remove orphaned worktree directories
    WORKTREE_BASE_DIR=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['worktree_base_dir'])" 2>/dev/null || echo "/tmp/hostaway-mcp-worktrees")

    if [[ -d "$WORKTREE_BASE_DIR" ]]; then
        # Check for empty or stale directories
        local stale_count=0
        for worktree_path in "${WORKTREE_BASE_DIR}"/*; do
            if [[ -d "$worktree_path" ]]; then
                # Check if worktree is still valid
                if ! git worktree list | grep -q "$(basename "$worktree_path")"; then
                    stale_count=$((stale_count + 1))
                    if [[ "$DRY_RUN" == "true" ]]; then
                        echo "  [DRY RUN] Would remove: $worktree_path"
                    else
                        echo "  Removing stale worktree: $(basename "$worktree_path")"
                        rm -rf "$worktree_path"
                    fi
                fi
            fi
        done

        if [[ $stale_count -eq 0 ]]; then
            echo "  ✓ No stale worktrees found"
        else
            if [[ "$DRY_RUN" != "true" ]]; then
                echo "  ✓ Removed ${stale_count} stale worktree(s)"
            fi
        fi
    else
        echo "  ! Worktree base directory not found: ${WORKTREE_BASE_DIR}"
    fi

    echo ""
}

# Clean old logs
clean_logs() {
    echo "Cleaning old logs (keeping last ${KEEP_LAST_N_LOGS} runs)..."

    if [[ ! -d "$LOGS_DIR" ]]; then
        echo "  ! Logs directory not found: ${LOGS_DIR}"
        return
    fi

    # Find execution state files (execution-*.json)
    local execution_files=()
    while IFS= read -r file; do
        execution_files+=("$file")
    done < <(find "$LOGS_DIR" -name "execution-*.json" -type f 2>/dev/null | sort -r)

    local total_executions=${#execution_files[@]}

    if [[ $total_executions -eq 0 ]]; then
        echo "  ! No execution state files found"
    elif [[ $total_executions -le $KEEP_LAST_N_LOGS ]]; then
        echo "  ✓ Only ${total_executions} execution(s) found, keeping all"
    else
        local to_remove=$((total_executions - KEEP_LAST_N_LOGS))
        echo "  Found ${total_executions} execution(s), removing ${to_remove} oldest"

        # Remove oldest execution files
        for ((i=KEEP_LAST_N_LOGS; i<total_executions; i++)); do
            local file="${execution_files[$i]}"
            if [[ "$DRY_RUN" == "true" ]]; then
                echo "    [DRY RUN] Would remove: $(basename "$file")"
            else
                echo "    Removing: $(basename "$file")"
                rm -f "$file"
            fi
        done

        if [[ "$DRY_RUN" != "true" ]]; then
            echo "  ✓ Removed ${to_remove} old execution state(s)"
        fi
    fi

    # Clean orphaned log files (worktree-*.log, test-runner-*.log, etc.)
    echo ""
    echo "  Cleaning orphaned log files..."

    local orphaned_logs=()
    while IFS= read -r file; do
        orphaned_logs+=("$file")
    done < <(find "$LOGS_DIR" -name "worktree-*.log" -o -name "test-runner-*.log" -o -name "mcp-inspector-*.log" 2>/dev/null)

    if [[ ${#orphaned_logs[@]} -eq 0 ]]; then
        echo "    ✓ No orphaned logs found"
    else
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "    [DRY RUN] Would remove ${#orphaned_logs[@]} orphaned log(s)"
        else
            for log_file in "${orphaned_logs[@]}"; do
                rm -f "$log_file"
            done
            echo "    ✓ Removed ${#orphaned_logs[@]} orphaned log(s)"
        fi
    fi

    # Clean old archives (keep last 5)
    echo ""
    echo "  Cleaning old log archives..."

    local archives=()
    while IFS= read -r file; do
        archives+=("$file")
    done < <(find "$LOGS_DIR" -name "rollback-archive-*.tar.gz" -type f 2>/dev/null | sort -r)

    if [[ ${#archives[@]} -le 5 ]]; then
        echo "    ✓ Only ${#archives[@]} archive(s) found, keeping all"
    else
        local to_remove=$((${#archives[@]} - 5))
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "    [DRY RUN] Would remove ${to_remove} oldest archive(s)"
        else
            for ((i=5; i<${#archives[@]}; i++)); do
                rm -f "${archives[$i]}"
            done
            echo "    ✓ Removed ${to_remove} old archive(s)"
        fi
    fi

    echo ""
}

# Clean orphaned branches
clean_branches() {
    echo "Cleaning orphaned branches..."

    BRANCH_PREFIX=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['branch_prefix'])" 2>/dev/null || echo "mcp-")

    # Find branches with prefix that don't have worktrees
    local orphaned_branches=()

    while IFS= read -r branch; do
        # Check if branch has an active worktree
        if ! git worktree list | grep -q "$branch"; then
            orphaned_branches+=("$branch")
        fi
    done < <(git branch --list "${BRANCH_PREFIX}*" --format='%(refname:short)')

    if [[ ${#orphaned_branches[@]} -eq 0 ]]; then
        echo "  ✓ No orphaned branches found"
    else
        echo "  Found ${#orphaned_branches[@]} orphaned branch(es):"

        for branch in "${orphaned_branches[@]}"; do
            if [[ "$DRY_RUN" == "true" ]]; then
                echo "    [DRY RUN] Would delete: ${branch}"
            else
                echo "    Deleting: ${branch}"
                if git branch -D "$branch" 2>/dev/null; then
                    echo "      ✓ Deleted local branch"
                fi

                # Try to delete remote branch
                if git push origin --delete "$branch" 2>/dev/null; then
                    echo "      ✓ Deleted remote branch"
                else
                    echo "      ! Remote branch may not exist"
                fi
            fi
        done

        if [[ "$DRY_RUN" != "true" ]]; then
            echo "  ✓ Cleaned ${#orphaned_branches[@]} orphaned branch(es)"
        fi
    fi

    echo ""
}

# Validate no orphaned branches
validate_branches() {
    echo "Validating branch state..."

    BRANCH_PREFIX=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['branch_prefix'])" 2>/dev/null || echo "mcp-")

    # Check for merged branches that can be deleted
    local merged_branches=()
    while IFS= read -r branch; do
        merged_branches+=("$branch")
    done < <(git branch --merged --list "${BRANCH_PREFIX}*" --format='%(refname:short)')

    if [[ ${#merged_branches[@]} -eq 0 ]]; then
        echo "  ✓ No merged branches to clean"
    else
        echo "  Found ${#merged_branches[@]} merged branch(es) that can be deleted:"
        for branch in "${merged_branches[@]}"; do
            echo "    - ${branch}"
        done

        if [[ "$DRY_RUN" != "true" ]]; then
            read -p "  Delete merged branches? (y/N): " -r
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                for branch in "${merged_branches[@]}"; do
                    git branch -d "$branch"
                done
                echo "  ✓ Deleted ${#merged_branches[@]} merged branch(es)"
            fi
        fi
    fi

    echo ""
}

# Main execution
main() {
    local clean_all=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --keep-logs)
                KEEP_LAST_N_LOGS="$2"
                shift 2
                ;;
            --all)
                clean_all=true
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
    echo "MCP Migration Cleanup"
    echo "========================================="

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
    fi

    echo ""

    # Execute cleanup tasks
    clean_worktrees

    clean_logs

    clean_branches

    validate_branches

    echo "========================================="
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}DRY RUN complete. Run without --dry-run to apply changes.${NC}"
    else
        echo -e "${GREEN}✅ Cleanup complete${NC}"
    fi
    echo "========================================="
}

main "$@"
