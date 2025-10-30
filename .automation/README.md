# Automated Parallel MCP Migration System

This directory contains the automation scripts for executing the MCP migration guide in parallel using git worktrees.

## Quick Start

```bash
# 1. Validate configuration
.automation/scripts/validate-config.sh

# 2. Preview execution plan (dry-run)
.automation/scripts/orchestrator.sh --dry-run

# 3. Execute migration
.automation/scripts/orchestrator.sh

# 4. Monitor progress (in another terminal)
.automation/scripts/status.sh --watch

# 5. Rollback if needed (emergency only)
.automation/scripts/rollback.sh
```

## Directory Structure

```
.automation/
├── config/                      # Configuration files
│   ├── dependency-graph.yaml    # Fix dependencies and execution order
│   ├── fix-definitions.yaml     # Fix metadata and requirements
│   └── worktree-config.yaml     # Worktree settings
├── scripts/                     # Automation scripts
│   ├── orchestrator.sh          # Main orchestrator (entry point)
│   ├── worktree-manager.sh      # Git worktree operations
│   ├── fix-executor.sh          # Execute individual fixes
│   ├── test-runner.sh           # Run tests for fixes
│   ├── pr-automation.sh         # Create and manage PRs
│   ├── state_manager.py         # Type-safe state management
│   ├── status.sh                # Monitor execution progress
│   ├── validate-config.sh       # Validate configuration
│   └── rollback.sh              # Emergency rollback
├── templates/                   # Code generation templates
│   ├── fix-template.j2          # Fix implementation template
│   └── test-template.j2         # Test generation template
└── logs/                        # Execution logs (gitignored)
    ├── orchestrator.log
    ├── worktree-*.log
    ├── execution-state.json
    └── summary-report.md
```

## Scripts Overview

### orchestrator.sh
Main entry point that coordinates parallel execution.

**Usage:**
```bash
# Full execution
./orchestrator.sh

# Dry run (preview only)
./orchestrator.sh --dry-run

# Execute specific fixes only
./orchestrator.sh --fixes "fix-1-service-prefixes,fix-2-tool-annotations"

# Debug mode with verbose logging
./orchestrator.sh --debug
```

**What it does:**
1. Creates checkpoint tag for rollback
2. Validates configuration
3. Resolves fix dependencies
4. Executes fixes in parallel waves
5. Creates PRs with auto-merge
6. Generates summary report

### worktree-manager.sh
Manages git worktrees for isolated parallel development.

**Usage:**
```bash
# Create worktree
./worktree-manager.sh create fix-1-service-prefixes

# List active worktrees
./worktree-manager.sh list

# Show worktree status
./worktree-manager.sh status fix-1-service-prefixes

# Delete worktree
./worktree-manager.sh delete fix-1-service-prefixes

# Clean up stale worktrees
./worktree-manager.sh prune
```

### fix-executor.sh
Executes a single fix within its worktree.

**Usage:**
```bash
# Execute fix
./fix-executor.sh fix-1-service-prefixes

# Dry run
./fix-executor.sh fix-1-service-prefixes --dry-run
```

**What it does:**
1. Applies fix to target file
2. Commits changes
3. Logs execution

### test-runner.sh
Runs tests for a fix.

**Usage:**
```bash
./test-runner.sh fix-1-service-prefixes
```

**What it does:**
1. Runs unit tests (pytest)
2. Runs MCP Inspector validation
3. Runs integration tests
4. Logs test results

### pr-automation.sh
Creates and manages pull requests.

**Usage:**
```bash
# Create PR
./pr-automation.sh create fix-1-service-prefixes

# Check PR status
./pr-automation.sh status fix-1-service-prefixes

# Manually merge PR
./pr-automation.sh merge fix-1-service-prefixes
```

**Requirements:**
- GitHub CLI (`gh`) installed and authenticated
- Repository access

### status.sh
Monitors real-time execution progress.

**Usage:**
```bash
# Show current status once
./status.sh

# Continuously monitor (updates every 5 seconds)
./status.sh --watch

# Get status as JSON
./status.sh --json
```

### rollback.sh
Emergency rollback to pre-migration state.

**Usage:**
```bash
# Interactive rollback (asks for confirmation)
./rollback.sh

# Force rollback (skip confirmation)
./rollback.sh --force
```

⚠️ **Warning:** This will:
- Stop all running worktrees
- Close all open PRs
- Reset main branch to checkpoint tag
- Delete all worktrees and branches

## Configuration Files

### dependency-graph.yaml
Defines fix dependencies and execution order.

```yaml
nodes:
  - fix-1-service-prefixes
  - fix-2-tool-annotations
  # ... 7 total fixes

edges:
  - from: fix-1-service-prefixes
    to: fix-4-response-formats

execution_order:
  - [fix-1, fix-2, fix-3, imp-1, imp-2, imp-3]  # Wave 1 (parallel)
  - [fix-4]                                       # Wave 2 (after Wave 1)
```

### fix-definitions.yaml
Metadata for each fix.

```yaml
fixes:
  - fix_id: fix-1-service-prefixes
    name: "Add Service Prefixes"
    description: "Add 'hostaway_' prefix to all tool names"
    estimated_duration_seconds: 7200
    target_file: mcp_stdio_server.py
    test_file: tests/mcp/test_tool_discovery.py
    dependencies: []
```

### worktree-config.yaml
Worktree and execution settings.

```yaml
worktree_base_dir: /tmp/hostaway-mcp-worktrees
branch_prefix: mcp-
base_branch: 001-we-need-to
auto_merge_enabled: true
fix_timeout: 7200  # 2 hours per fix
```

## Execution Flow

```
1. orchestrator.sh starts
   ├── Creates checkpoint tag (rollback point)
   ├── Validates configuration
   ├── Loads execution order from dependency graph
   └── Resolves dependency waves

2. Wave 1 Execution (6 fixes in parallel)
   ├── fix-1: worktree-manager.sh create → fix-executor.sh → test-runner.sh → pr-automation.sh
   ├── fix-2: worktree-manager.sh create → fix-executor.sh → test-runner.sh → pr-automation.sh
   ├── fix-3: worktree-manager.sh create → fix-executor.sh → test-runner.sh → pr-automation.sh
   ├── imp-1: worktree-manager.sh create → fix-executor.sh → test-runner.sh → pr-automation.sh
   ├── imp-2: worktree-manager.sh create → fix-executor.sh → test-runner.sh → pr-automation.sh
   └── imp-3: worktree-manager.sh create → fix-executor.sh → test-runner.sh → pr-automation.sh
   └── Wait for all Wave 1 fixes to complete

3. Wave 2 Execution (1 fix, depends on Wave 1)
   └── fix-4: worktree-manager.sh create → fix-executor.sh → test-runner.sh → pr-automation.sh

4. PR Auto-Merge
   └── GitHub Actions CI passes → Auto-merge enabled → PRs merge sequentially

5. Cleanup (on success)
   └── Delete worktrees, generate summary report
```

## State Management

The system maintains execution state in `.automation/logs/execution-state.json`:

```json
{
  "execution_id": "mcp-migration-20251030-143022",
  "start_time": "2025-10-30T14:30:22Z",
  "status": "in_progress",
  "worktrees": [
    {
      "fix_id": "fix-1-service-prefixes",
      "status": "complete",
      "pr_number": 123,
      "test_results": {
        "unit_tests_pass": true,
        "mcp_inspector_pass": true,
        "coverage_percent": 85.2
      }
    }
  ]
}
```

Access state programmatically:

```bash
# Initialize state
./state_manager.py init .automation/logs/execution-state.json

# Load state
./state_manager.py load .automation/logs/execution-state.json

# Get summary
./state_manager.py summary .automation/logs/execution-state.json
```

## Monitoring

### Real-Time Monitoring
```bash
# Terminal 1: Run orchestrator
./orchestrator.sh

# Terminal 2: Watch progress
./status.sh --watch
```

### View Logs
```bash
# Main orchestrator log
tail -f .automation/logs/orchestrator.log

# Specific worktree log
tail -f .automation/logs/worktree-fix-1-service-prefixes.log

# Test results
cat .automation/logs/test-results/fix-1-*.log
```

## Troubleshooting

### Issue: Configuration validation fails
**Solution:**
```bash
# Check YAML syntax
.automation/scripts/validate-config.sh

# Verify all required fields present
cat .automation/config/fix-definitions.yaml | grep -A 10 "fix_id"
```

### Issue: Worktree creation fails
**Solution:**
```bash
# Clean up stale worktrees
git worktree prune
rm -rf /tmp/hostaway-mcp-worktrees/*

# Re-run orchestrator
./orchestrator.sh
```

### Issue: PR creation fails
**Solution:**
```bash
# Check GitHub CLI authentication
gh auth status

# Re-authenticate if needed
gh auth login

# Manually create PR
cd /tmp/hostaway-mcp-worktrees/fix-1-service-prefixes
gh pr create --base 001-we-need-to --head mcp-fix-1-service-prefixes
```

### Issue: Tests failing
**Solution:**
```bash
# Run tests manually in worktree
cd /tmp/hostaway-mcp-worktrees/fix-1-service-prefixes
uv run pytest tests/mcp/test_tool_discovery.py -v

# View test logs
cat .automation/logs/worktree-fix-1-service-prefixes.log
```

## Best Practices

1. **Always run dry-run first:**
   ```bash
   ./orchestrator.sh --dry-run
   ```

2. **Monitor in separate terminal:**
   ```bash
   ./status.sh --watch
   ```

3. **Check logs if failures occur:**
   ```bash
   tail -f .automation/logs/orchestrator.log
   ```

4. **Keep checkpoint tag safe:**
   - Never delete checkpoint tags until migration verified
   - Tag stored in `.automation/logs/checkpoint-tag.txt`

5. **Test configuration after changes:**
   ```bash
   ./validate-config.sh
   ```

## Performance

**Expected Duration:**
- **Sequential**: 12-16 hours (1 fix at a time)
- **Parallel**: ~4 hours (7 fixes in 2 waves)
- **Time Saved**: 70% faster

**Resource Usage:**
- **Disk**: ~2GB (7 worktrees)
- **Memory**: ~500MB
- **CPU**: Varies (parallel pytest/MCP Inspector)

## Development

### Adding a New Fix

1. **Update `fix-definitions.yaml`:**
   ```yaml
   - fix_id: fix-8-new-feature
     name: "New Feature"
     description: "Description"
     estimated_duration_seconds: 3600
     target_file: mcp_stdio_server.py
     test_file: tests/mcp/test_new_feature.py
     dependencies: []
   ```

2. **Update `dependency-graph.yaml`:**
   ```yaml
   nodes:
     - fix-8-new-feature

   # Add dependencies if needed
   edges:
     - from: fix-1-service-prefixes
       to: fix-8-new-feature

   execution_order:
     - [fix-1, fix-2, ..., fix-8-new-feature]
   ```

3. **Implement fix logic in `fix-executor.sh`:**
   ```bash
   apply_fix_8_new_feature() {
       echo "  Applying Fix 8: New Feature..."
       # Implementation here
   }
   ```

4. **Validate configuration:**
   ```bash
   ./validate-config.sh
   ```

5. **Test with dry-run:**
   ```bash
   ./orchestrator.sh --fixes "fix-8-new-feature" --dry-run
   ```

## See Also

- [MCP Migration Guide](../docs/MCP_MIGRATION_GUIDE.md) - Detailed fix descriptions
- [Quickstart Guide](../specs/010-we-need-to/quickstart.md) - User-facing guide
- [Feature Specification](../specs/010-we-need-to/spec.md) - Complete feature spec
- [Tasks Breakdown](../specs/010-we-need-to/tasks.md) - Implementation tasks
