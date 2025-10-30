# Quickstart: Automated Parallel MCP Migration

**Feature**: 010-we-need-to | **Last Updated**: 2025-10-30

## Overview

This guide explains how to run the automated MCP migration system that executes all 7 fixes from `docs/MCP_MIGRATION_GUIDE.md` in parallel using git worktrees.

**Expected Duration**: ~4 hours (unattended)
**Manual Intervention**: None required
**Prerequisites**: Git 2.35+, GitHub CLI, Python 3.12+, uv, Node.js (for MCP Inspector)

---

## Quick Start

### 1. Prerequisites Check

```bash
# Verify git version (need 2.35+)
git --version

# Verify GitHub CLI is authenticated
gh auth status

# Verify uv is installed
uv --version

# Verify MCP Inspector available
npx @modelcontextprotocol/inspector --version

# Verify on correct branch
git branch --show-current  # Should be 001-we-need-to or similar
```

### 2. Run Migration

```bash
# From repo root
.automation/scripts/orchestrator.sh

# That's it! The script will:
# - Create checkpoint tag
# - Create 7 worktrees in /tmp/
# - Execute fixes in parallel
# - Run tests for each fix
# - Create PRs
# - Auto-merge after CI passes
# - Clean up worktrees
# - Generate summary report
```

### 3. Monitor Progress

```bash
# In another terminal, watch progress
watch -n 5 .automation/scripts/status.sh

# Or query once
.automation/scripts/status.sh

# View logs
tail -f .automation/logs/orchestrator.log

# View specific worktree log
tail -f .automation/logs/worktree-fix-1-service-prefixes.log
```

### 4. Review Results

```bash
# After completion, view summary
cat .automation/logs/summary-report.md

# Check PRs created
gh pr list --label mcp-migration

# Verify MCP compliance
npx @modelcontextprotocol/inspector mcp_stdio_server.py

# Run integration tests
pytest tests/mcp/ -v
```

---

## Advanced Usage

### Rollback

If something goes wrong and you need to rollback:

```bash
# Emergency rollback to pre-migration state
.automation/scripts/rollback.sh

# This will:
# - Stop all worktrees
# - Close all PRs
# - Reset main branch to checkpoint
# - Clean up temporary files
```

### Dry Run

Test the orchestration without making changes:

```bash
.automation/scripts/orchestrator.sh --dry-run

# Shows:
# - Worktrees that would be created
# - Dependency resolution order
# - Estimated completion time
# - Does NOT create worktrees or PRs
```

### Partial Execution

Run only specific fixes:

```bash
# Run only high-priority fixes (1-4)
.automation/scripts/orchestrator.sh --fixes "fix-1,fix-2,fix-3,fix-4"

# Run only a single fix (useful for debugging)
.automation/scripts/orchestrator.sh --fixes "fix-1-service-prefixes"
```

### Debug Mode

Enable verbose logging:

```bash
.automation/scripts/orchestrator.sh --debug

# Logs every command executed
# Useful for troubleshooting
```

---

## Configuration

### Environment Variables

```bash
# Optional: Override default worktree location
export WORKTREE_BASE_DIR="/custom/path"  # Default: /tmp/hostaway-mcp-worktrees

# Optional: Override base branch
export BASE_BRANCH="main"  # Default: 001-we-need-to

# Optional: Override timeout per fix (seconds)
export FIX_TIMEOUT=10800  # Default: 7200 (2 hours)

# Optional: Disable auto-merge (manual PR merging)
export AUTO_MERGE=false  # Default: true
```

### Config Files

Edit `.automation/config/` files to customize behavior:

**dependency-graph.yaml**: Modify fix dependencies
```yaml
dependencies:
  - from: fix-1-service-prefixes
    to: fix-4-markdown-support
  - from: fix-3-error-messages
    to: fix-4-markdown-support
```

**worktree-config.yaml**: Adjust worktree settings
```yaml
worktree_base_dir: /tmp/hostaway-mcp-worktrees
branch_prefix: mcp-
cleanup_on_success: true
cleanup_on_failure: false
```

---

## Troubleshooting

### Issue: Worktree creation fails

**Symptom**: `git worktree add` fails with "path already exists"

**Solution**:
```bash
# Clean up stale worktrees
git worktree prune
rm -rf /tmp/hostaway-mcp-worktrees/*

# Re-run orchestrator
.automation/scripts/orchestrator.sh
```

### Issue: Test failures in multiple fixes

**Symptom**: 3+ fixes fail tests

**Solution**:
```bash
# Rollback to checkpoint
.automation/scripts/rollback.sh

# Review failed test logs
cat .automation/logs/test-results/fix-*.log

# Fix underlying issue
# Re-run migration
.automation/scripts/orchestrator.sh
```

### Issue: PR auto-merge not working

**Symptom**: PRs created but not merging

**Solution**:
```bash
# Check CI status
gh pr checks

# If CI failed, view details
gh pr view <pr-number> --web

# If CI passing but not merging, check auto-merge enabled
gh pr view <pr-number> --json autoMergeRequest
```

### Issue: Out of disk space

**Symptom**: Error during worktree creation

**Solution**:
```bash
# Check disk usage
df -h /tmp/

# Worktrees use ~2GB total
# Ensure at least 3GB available in /tmp/

# Clean up old worktrees
git worktree prune
rm -rf /tmp/hostaway-mcp-worktrees/*
```

---

## Understanding the Output

### Status Output Example

```
MCP Migration Status
==================
✅ Fix 1 (Service Prefixes)  [COMPLETE] PR #123 merged in 1h 15m
🔄 Fix 2 (Annotations)       [TESTING] Running pytest...
🔄 Fix 3 (Error Messages)    [IN PROGRESS] Implementing error handlers...
⏸️  Fix 4 (Markdown)          [WAITING] Depends on: Fix 1 ✅, Fix 3 🔄
✅ Imp 1 (Descriptions)       [COMPLETE] PR #124 merged in 2h 30m
🔄 Imp 2 (Validation)        [TESTING] Running MCP Inspector...
🔄 Imp 3 (Truncation)        [IN PROGRESS] Adding truncation logic...

Progress: 2/7 complete (28%) | Est. completion: 2h 15m
Parallel efficiency: 65% | Time saved: 8h 30m vs sequential
```

### Summary Report Example

```markdown
# MCP Migration Summary Report

**Execution ID**: mcp-migration-20251030-143022
**Duration**: 3h 45m (vs 12-16h sequential)
**Time Saved**: 70% faster

## Results
✅ 7/7 fixes completed successfully
✅ All tests pass (coverage: 82.5%)
✅ MCP Inspector: 10/10 compliance
✅ Integration tests: PASS

## PRs Created & Merged
- #123: Fix 1 - Service Prefixes (merged)
- #124: Fix 2 - Tool Annotations (merged)
- #125: Fix 3 - Error Messages (merged)
- #126: Fix 4 - Markdown Support (merged)
- #127: Imp 1 - Tool Descriptions (merged)
- #128: Imp 2 - Input Validation (merged)
- #129: Imp 3 - CHARACTER_LIMIT (merged)

## Metrics
- Worktrees created: 7
- Parallel execution waves: 2
- Average fix duration: 1h 52m
- Longest fix: Fix 4 (3h 35m)
- Shortest fix: Fix 2 (28m)

## Next Steps
✅ Migration complete - ready for production deployment
```

---

## FAQ

**Q: Can I run this multiple times?**
A: Yes, but only if previous run completed or was rolled back. Active worktrees will block new runs.

**Q: What if I need to pause execution?**
A: There's no pause mechanism. You can stop with Ctrl+C and rollback, or let it complete then revert commits.

**Q: Can I modify fixes during execution?**
A: No. Fixes are applied automatically from migration guide. Customization requires editing the guide first.

**Q: How do I add a new fix?**
A: Add to `docs/MCP_MIGRATION_GUIDE.md`, update `.automation/config/fix-definitions.yaml`, and re-run.

**Q: What if CI checks fail?**
A: Auto-merge will not occur. Review CI logs, fix issues, and manually merge or re-run migration.

**Q: Can I run this on a remote server?**
A: Yes, but ensure GitHub CLI is authenticated and you have SSH access for monitoring logs.

---

## Support

**Logs Location**: `.automation/logs/`
**Config Location**: `.automation/config/`
**Documentation**: `specs/010-we-need-to/`

**Report Issues**: Include `.automation/logs/orchestrator.log` and `.automation/logs/execution-state.json`
