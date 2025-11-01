#!/usr/bin/env bash
# Git Worktree Manager for MCP Migration
# Provides CRUD operations for git worktrees

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../config"
LOGS_DIR="${SCRIPT_DIR}/../logs"

# Load configuration
if [[ -f "${CONFIG_DIR}/worktree-config.yaml" ]]; then
    WORKTREE_BASE_DIR=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['worktree_base_dir'])")
    BRANCH_PREFIX=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['branch_prefix'])")
    BASE_BRANCH=$(python3 -c "import yaml; print(yaml.safe_load(open('${CONFIG_DIR}/worktree-config.yaml'))['base_branch'])")
else
    echo "ERROR: worktree-config.yaml not found"
    exit 1
fi

# Usage information
usage() {
    cat <<EOF
Usage: $(basename "$0") <command> [options]

Commands:
    create <fix_id>     Create a new worktree for the given fix
    delete <fix_id>     Delete a worktree
    list                List all active worktrees
    prune               Clean up stale worktrees
    status <fix_id>     Show status of a specific worktree

Options:
    -h, --help          Show this help message

Examples:
    $(basename "$0") create fix-1-service-prefixes
    $(basename "$0") delete fix-1-service-prefixes
    $(basename "$0") list
    $(basename "$0") status fix-1-service-prefixes
EOF
}

# Create worktree for a fix
create_worktree() {
    local fix_id="$1"
    local branch_name="${BRANCH_PREFIX}${fix_id}"
    local worktree_path="${WORKTREE_BASE_DIR}/${fix_id}"

    echo "Creating worktree for ${fix_id}..."
    echo "  Branch: ${branch_name}"
    echo "  Path: ${worktree_path}"

    # Ensure base directory exists
    mkdir -p "${WORKTREE_BASE_DIR}"

    # Check if worktree already exists
    if [[ -d "${worktree_path}" ]]; then
        echo "ERROR: Worktree already exists at ${worktree_path}"
        exit 1
    fi

    # Check if branch already exists
    if git show-ref --verify --quiet refs/heads/"${branch_name}"; then
        echo "ERROR: Branch ${branch_name} already exists"
        echo "  Use 'git branch -D ${branch_name}' to delete it first"
        exit 1
    fi

    # Create worktree
    if git worktree add -b "${branch_name}" "${worktree_path}" "${BASE_BRANCH}"; then
        echo "✓ Worktree created successfully"
        echo "  Path: ${worktree_path}"
        echo "  Branch: ${branch_name}"

        # Log worktree creation
        echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | CREATE | ${fix_id} | ${worktree_path}" >> "${LOGS_DIR}/worktree.log"

        return 0
    else
        echo "ERROR: Failed to create worktree"
        return 1
    fi
}

# Delete worktree
delete_worktree() {
    local fix_id="$1"
    local branch_name="${BRANCH_PREFIX}${fix_id}"
    local worktree_path="${WORKTREE_BASE_DIR}/${fix_id}"

    echo "Deleting worktree for ${fix_id}..."

    # Check if worktree exists
    if [[ ! -d "${worktree_path}" ]]; then
        echo "WARNING: Worktree not found at ${worktree_path}"
        # Try to remove from git's worktree list anyway
        git worktree remove "${worktree_path}" --force 2>/dev/null || true
        return 0
    fi

    # Remove worktree
    if git worktree remove "${worktree_path}" --force; then
        echo "✓ Worktree removed successfully"

        # Log worktree deletion
        echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | DELETE | ${fix_id} | ${worktree_path}" >> "${LOGS_DIR}/worktree.log"

        return 0
    else
        echo "ERROR: Failed to remove worktree"
        return 1
    fi
}

# List all worktrees
list_worktrees() {
    echo "Active worktrees:"
    echo ""

    git worktree list --porcelain | awk '
        /^worktree / { path = $2 }
        /^branch / {
            branch = $2
            gsub(/^refs\/heads\//, "", branch)
            if (path != "") {
                printf "%-50s %s\n", path, branch
                path = ""
            }
        }
    '
}

# Prune stale worktrees
prune_worktrees() {
    echo "Pruning stale worktrees..."

    if git worktree prune -v; then
        echo "✓ Pruning complete"

        # Log prune operation
        echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | PRUNE | - | -" >> "${LOGS_DIR}/worktree.log"

        return 0
    else
        echo "ERROR: Failed to prune worktrees"
        return 1
    fi
}

# Show status of a specific worktree
status_worktree() {
    local fix_id="$1"
    local worktree_path="${WORKTREE_BASE_DIR}/${fix_id}"

    if [[ ! -d "${worktree_path}" ]]; then
        echo "Worktree not found: ${fix_id}"
        return 1
    fi

    echo "Worktree status for ${fix_id}:"
    echo "  Path: ${worktree_path}"
    echo ""

    # Change to worktree directory and show status
    (cd "${worktree_path}" && git status)
}

# Main command dispatcher
main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi

    case "$1" in
        create)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: Missing fix_id argument"
                usage
                exit 1
            fi
            create_worktree "$2"
            ;;
        delete)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: Missing fix_id argument"
                usage
                exit 1
            fi
            delete_worktree "$2"
            ;;
        list)
            list_worktrees
            ;;
        prune)
            prune_worktrees
            ;;
        status)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: Missing fix_id argument"
                usage
                exit 1
            fi
            status_worktree "$2"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

main "$@"
