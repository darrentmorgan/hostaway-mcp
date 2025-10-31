#!/usr/bin/env bash
# Validate configuration files before running orchestration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/../config"

echo "Validating MCP Migration configuration..."

# Check required files exist
required_files=(
    "${CONFIG_DIR}/dependency-graph.yaml"
    "${CONFIG_DIR}/fix-definitions.yaml"
    "${CONFIG_DIR}/worktree-config.yaml"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "ERROR: Required config file missing: $file"
        exit 1
    fi
done

echo "✓ All required config files present"

# Validate YAML syntax
if command -v python3 &>/dev/null; then
    python3 <<EOF
import yaml
import sys

files = [
    "${CONFIG_DIR}/dependency-graph.yaml",
    "${CONFIG_DIR}/fix-definitions.yaml",
    "${CONFIG_DIR}/worktree-config.yaml"
]

for file_path in files:
    try:
        with open(file_path) as f:
            yaml.safe_load(f)
        print(f"✓ Valid YAML: {file_path}")
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in {file_path}: {e}")
        sys.exit(1)
EOF
else
    echo "WARNING: python3 not found, skipping YAML validation"
fi

# Validate dependency graph structure
echo "Validating dependency graph..."
python3 <<EOF
import yaml

with open("${CONFIG_DIR}/dependency-graph.yaml") as f:
    graph = yaml.safe_load(f)

# Check required keys
required_keys = ["nodes", "edges", "execution_order"]
for key in required_keys:
    if key not in graph:
        print(f"ERROR: Missing required key '{key}' in dependency-graph.yaml")
        exit(1)

# Check all nodes exist
nodes = set(graph["nodes"])
if len(nodes) != 7:
    print(f"ERROR: Expected 7 nodes, found {len(nodes)}")
    exit(1)

# Check edges reference valid nodes
for edge in graph["edges"]:
    if edge["from"] not in nodes:
        print(f"ERROR: Edge references unknown node: {edge['from']}")
        exit(1)
    if edge["to"] not in nodes:
        print(f"ERROR: Edge references unknown node: {edge['to']}")
        exit(1)

# Check execution order covers all nodes
order_nodes = set()
for wave in graph["execution_order"]:
    order_nodes.update(wave)

if order_nodes != nodes:
    print(f"ERROR: Execution order doesn't match nodes")
    print(f"  Missing: {nodes - order_nodes}")
    print(f"  Extra: {order_nodes - nodes}")
    exit(1)

print("✓ Dependency graph structure valid")
EOF

# Validate fix definitions
echo "Validating fix definitions..."
python3 <<EOF
import yaml

with open("${CONFIG_DIR}/fix-definitions.yaml") as f:
    definitions = yaml.safe_load(f)

if "fixes" not in definitions:
    print("ERROR: Missing 'fixes' key in fix-definitions.yaml")
    exit(1)

fixes = definitions["fixes"]
if len(fixes) != 7:
    print(f"ERROR: Expected 7 fixes, found {len(fixes)}")
    exit(1)

required_fields = [
    "fix_id", "fix_number", "fix_type", "name", "description",
    "migration_guide_section", "estimated_duration_seconds",
    "target_file", "lines_added", "test_file", "dependencies"
]

for fix in fixes:
    for field in required_fields:
        if field not in fix:
            print(f"ERROR: Fix {fix.get('fix_id', '?')} missing required field: {field}")
            exit(1)

    # Validate fix_id pattern
    fix_id = fix["fix_id"]
    if not (fix_id.startswith("fix-") or fix_id.startswith("imp-")):
        print(f"ERROR: Invalid fix_id format: {fix_id}")
        exit(1)

    # Validate fix_type
    if fix["fix_type"] not in ["high_priority", "medium_priority"]:
        print(f"ERROR: Invalid fix_type for {fix_id}: {fix['fix_type']}")
        exit(1)

print("✓ Fix definitions valid")
EOF

# Validate worktree config
echo "Validating worktree config..."
python3 <<EOF
import yaml

with open("${CONFIG_DIR}/worktree-config.yaml") as f:
    config = yaml.safe_load(f)

required_keys = [
    "worktree_base_dir", "branch_prefix", "base_branch",
    "cleanup_on_success", "cleanup_on_failure",
    "fix_timeout", "test_timeout", "pr_creation_timeout",
    "auto_merge_enabled", "auto_merge_method", "delete_branch_after_merge",
    "max_concurrent_worktrees"
]

for key in required_keys:
    if key not in config:
        print(f"ERROR: Missing required key '{key}' in worktree-config.yaml")
        exit(1)

# Validate timeouts are positive
for timeout_key in ["fix_timeout", "test_timeout", "pr_creation_timeout"]:
    if config[timeout_key] <= 0:
        print(f"ERROR: {timeout_key} must be positive")
        exit(1)

# Validate max_concurrent_worktrees
if config["max_concurrent_worktrees"] < 1 or config["max_concurrent_worktrees"] > 7:
    print(f"ERROR: max_concurrent_worktrees must be 1-7")
    exit(1)

print("✓ Worktree config valid")
EOF

echo ""
echo "✅ All configuration files are valid"
echo "Ready to run orchestrator.sh"
