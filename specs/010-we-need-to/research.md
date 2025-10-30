# Research: Automated Parallel MCP Migration

**Feature**: 010-we-need-to | **Date**: 2025-10-30
**Phase**: 0 - Outline & Research

## Research Questions

### Q1: Git Worktree Best Practices for Parallel Development

**Decision**: Use isolated worktrees in `/tmp/` with separate branches per fix

**Rationale**:
- Git worktrees allow multiple branches checked out simultaneously
- Each worktree is a complete working directory with its own staging area
- Worktrees share the same `.git` directory (saves disk space)
- Isolation prevents interference between parallel implementations
- `/tmp/` location avoids cluttering main repo

**Implementation Details**:
```bash
# Create worktree
git worktree add /tmp/hostaway-mcp-worktrees/fix-1-service-prefixes -b mcp-fix-1-service-prefixes

# Work in isolation
cd /tmp/hostaway-mcp-worktrees/fix-1-service-prefixes
# Make changes, commit, push

# Cleanup after merge
git worktree remove /tmp/hostaway-mcp-worktrees/fix-1-service-prefixes
git branch -d mcp-fix-1-service-prefixes
```

**Alternatives Considered**:
1. **Multiple clones**: Rejected - wastes disk space (~2GB per clone × 7 = 14GB)
2. **Stashing/branch switching**: Rejected - not truly parallel, requires coordination
3. **Docker containers**: Rejected - adds complexity, resource overhead

**Best Practices Applied**:
- Use descriptive branch names: `mcp-fix-{number}-{short-name}`
- Lock shared resources (main branch) during merge operations
- Clean up worktrees immediately after successful merge
- Use absolute paths to avoid path confusion

**References**:
- Git Worktree Documentation: https://git-scm.com/docs/git-worktree
- Pro Git Chapter on Worktrees: https://git-scm.com/book/en/v2

---

### Q2: Dependency Resolution Strategy for Parallel Tasks

**Decision**: Use directed acyclic graph (DAG) with topological sort for execution ordering

**Rationale**:
- Fix 4 (Markdown) depends on Fix 1 (service prefixes) for renamed tool names
- Fix 4 also depends on Fix 3 (error messages) for error helper functions
- Fixes 2, 5, 6, 7 are independent and can execute freely
- DAG ensures dependencies execute before dependents
- Topological sort provides valid execution order

**Dependency Graph**:
```
Fix 1 (Service Prefixes) ──┐
                             ├─→ Fix 4 (Markdown Support)
Fix 3 (Error Messages) ─────┘

Fix 2 (Annotations) ──────────→ (independent)
Imp 1 (Descriptions) ─────────→ (independent)
Imp 2 (Input Validation) ─────→ (independent)
Imp 3 (Character Limit) ──────→ (independent)
```

**Implementation Strategy**:
1. **Parallel Phase 1**: Start Fix 1, Fix 2, Fix 3, Imp 1, Imp 2, Imp 3 simultaneously
2. **Wait Gate**: Fix 4 waits until both Fix 1 AND Fix 3 complete
3. **Parallel Phase 2**: Fix 4 starts once dependencies satisfied
4. **Merge Phase**: Sequential merging in dependency order (Fix 1 → Fix 3 → Fix 4 → others)

**Conflict Resolution**:
- All fixes modify same file (`mcp_stdio_server.py`)
- Merges must be sequential to avoid conflicts
- Merge order follows dependency graph
- If merge conflict detected: attempt auto-resolution, else mark for manual review

**Alternatives Considered**:
1. **Sequential execution**: Rejected - defeats parallelization purpose (4 hours → 12-16 hours)
2. **No dependency tracking**: Rejected - would cause broken builds (Fix 4 using old tool names)
3. **Manual coordination**: Rejected - requires user input (violates "afk" requirement)

**Implementation Tools**:
- YAML config file: `.automation/config/dependency-graph.yaml`
- Bash associative arrays for graph representation
- Simple topological sort algorithm in bash

**References**:
- Topological Sorting: https://en.wikipedia.org/wiki/Topological_sorting
- DAG in Build Systems: https://martinfowler.com/articles/continuousIntegration.html

---

### Q3: Automated Testing Strategy Per Fix

**Decision**: Three-tier testing - unit tests, MCP Inspector validation, integration tests

**Rationale**:
- Each fix must be independently testable
- Migration guide already defines test scenarios per fix
- MCP Inspector provides protocol compliance validation
- pytest framework already in place

**Test Tiers**:

**Tier 1: Unit Tests (per fix)**
- Test specific functionality added by fix
- Mock external dependencies
- Fast execution (<30 seconds per fix)
- Example for Fix 1 (Service Prefixes):
  ```python
  def test_tool_names_have_hostaway_prefix():
      tools = list_tools()
      for tool in tools:
          assert tool.name.startswith("hostaway_"), f"Tool {tool.name} missing prefix"
  ```

**Tier 2: MCP Inspector Validation**
- Protocol compliance check
- Schema validation
- Tool discovery verification
- Example:
  ```bash
  npx @modelcontextprotocol/inspector mcp_stdio_server.py \
    --validate-tools \
    --check-annotations \
    --verify-schemas
  ```

**Tier 3: Integration Tests (merged state)**
- End-to-end workflows from migration guide
- All 7 test scenarios from guide (list properties, get details, error handling, etc.)
- Run only after all fixes merged

**Test Execution Flow**:
```
1. Fix Implementation Complete
   ↓
2. Run Unit Tests (pytest tests/automation/test_fix_{n}.py)
   ↓
3. Run MCP Inspector (validate protocol compliance)
   ↓
4. If PASS: Mark fix ready for merge
   If FAIL: Log error, retry once, then mark failed
   ↓
5. After All Fixes Merged: Run Integration Tests
```

**Coverage Requirements**:
- Each fix adds ~26 lines of code average
- Must maintain project-wide 80% coverage threshold
- New test file: `tests/mcp/test_mcp_stdio_improvements.py` (defined in migration guide)

**Alternatives Considered**:
1. **Manual testing**: Rejected - requires user input
2. **Integration tests only**: Rejected - slow feedback loop, hard to isolate failures
3. **No MCP Inspector**: Rejected - protocol compliance is critical

**References**:
- Migration Guide Testing Strategy: `docs/MCP_MIGRATION_GUIDE.md` lines 1328-1468
- MCP Inspector: https://modelcontextprotocol.io/docs/tools/inspector

---

### Q4: GitHub PR Automation with `gh` CLI

**Decision**: Use `gh pr create` and `gh pr merge` with auto-merge enabled

**Rationale**:
- `gh` CLI is already a project dependency
- Supports auto-merge after CI checks pass
- Can create PRs with templated descriptions
- Can merge PRs programmatically

**PR Creation Flow**:
```bash
# In worktree after successful tests
gh pr create \
  --base 001-we-need-to \
  --head mcp-fix-1-service-prefixes \
  --title "fix(mcp): add service prefixes to all MCP tool names" \
  --body "$(cat .automation/templates/pr-body.md)" \
  --label "mcp-migration,automated"

# Enable auto-merge
gh pr merge mcp-fix-1-service-prefixes \
  --auto \
  --squash \
  --delete-branch
```

**PR Description Template**:
```markdown
## MCP Migration: Fix {number} - {name}

**Migration Guide Reference**: `docs/MCP_MIGRATION_GUIDE.md` Fix {number}

**What**: {brief description}
**Why**: {MCP best practice compliance}

### Changes
- {list of changes from migration guide}

### Testing
- ✅ Unit tests pass
- ✅ MCP Inspector validation pass
- ✅ Coverage threshold maintained

### Dependency Status
{if dependencies exist}
- Depends on: #{pr-number-of-dependency}
- Will auto-merge after dependency merges

🤖 Generated with automated MCP migration workflow
```

**Auto-Merge Strategy**:
1. PR created with auto-merge enabled
2. CI/CD pipeline runs (GitHub Actions)
3. Once all checks pass, GitHub automatically merges
4. Dependency-aware: Fix 4 PR waits for Fix 1 and Fix 3 to merge before its CI runs

**Rate Limiting**:
- GitHub API allows 5000 requests/hour authenticated
- 7 PRs created simultaneously = 7 requests
- Well within limits, no throttling needed

**Alternatives Considered**:
1. **Manual PR creation**: Rejected - requires user input
2. **Direct push to main**: Rejected - bypasses CI/CD, violates best practices
3. **GitHub Actions workflow**: Rejected - more complex, less flexible than bash scripts

**References**:
- GitHub CLI PR Commands: https://cli.github.com/manual/gh_pr
- Auto-Merge Documentation: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request

---

### Q5: Rollback Mechanism for Failed Migrations

**Decision**: Tag-based rollback with automated branch reset

**Rationale**:
- Need ability to restore to pre-migration state if critical failure occurs
- Git tags provide immutable snapshots
- Can reset branches to tagged state
- Preserves work-in-progress for debugging

**Rollback Strategy**:

**Pre-Migration Checkpoint**:
```bash
# Tag current state before starting
git tag -a "pre-mcp-migration-$(date +%Y%m%d-%H%M%S)" -m "Checkpoint before automated MCP migration"
git push origin --tags
```

**Trigger Conditions**:
- 3+ fixes fail tests
- Critical security issue detected
- Main branch becomes unstable (tests fail)
- User manually triggers rollback

**Rollback Procedure**:
```bash
# 1. Stop all active worktrees
for worktree in /tmp/hostaway-mcp-worktrees/*; do
    kill $(cat $worktree/.pid) 2>/dev/null
done

# 2. Remove all feature branches
for branch in $(git branch | grep mcp-fix); do
    git branch -D $branch
done

# 3. Reset main branch to tagged state
git checkout 001-we-need-to
git reset --hard pre-mcp-migration-{timestamp}
git push origin 001-we-need-to --force-with-lease

# 4. Close all open PRs
gh pr list --label mcp-migration --json number | \
    jq -r '.[].number' | \
    xargs -I {} gh pr close {}

# 5. Clean up worktrees
git worktree prune
rm -rf /tmp/hostaway-mcp-worktrees
```

**Partial Rollback**:
- If only 1-2 fixes fail, keep successful ones merged
- Roll back only failed fixes
- Useful for iterative debugging

**Alternatives Considered**:
1. **No rollback**: Rejected - too risky, violates production safety requirement
2. **Full backup**: Rejected - expensive, slow to restore
3. **Manual intervention**: Rejected - violates "afk" requirement

**Implementation**:
- Script: `.automation/scripts/rollback.sh`
- Triggered by: orchestrator on failure threshold OR manual command
- Logs preserved: `.automation/logs/rollback-{timestamp}.log`

**References**:
- Git Reset Documentation: https://git-scm.com/docs/git-reset
- GitHub CLI PR Close: https://cli.github.com/manual/gh_pr_close

---

### Q6: Progress Monitoring and Status Reporting

**Decision**: JSON-based state file with real-time updates, terminal dashboard

**Rationale**:
- Need visibility into parallel execution status
- JSON format easily parseable
- Can query status without interrupting execution
- Terminal dashboard for human-readable view

**State Tracking**:

**State File Structure** (`.automation/logs/execution-state.json`):
```json
{
  "execution_id": "mcp-migration-20251030-143022",
  "start_time": "2025-10-30T14:30:22Z",
  "status": "in_progress",
  "fixes": {
    "fix-1-service-prefixes": {
      "status": "complete",
      "branch": "mcp-fix-1-service-prefixes",
      "worktree_path": "/tmp/hostaway-mcp-worktrees/fix-1-service-prefixes",
      "start_time": "2025-10-30T14:30:25Z",
      "end_time": "2025-10-30T15:45:12Z",
      "duration_seconds": 4487,
      "test_status": "pass",
      "pr_number": 123,
      "pr_status": "merged"
    },
    "fix-4-markdown-support": {
      "status": "waiting",
      "dependencies": ["fix-1-service-prefixes", "fix-3-error-messages"],
      "dependencies_met": ["fix-1-service-prefixes"],
      "dependencies_pending": ["fix-3-error-messages"]
    }
  },
  "summary": {
    "total_fixes": 7,
    "completed": 2,
    "in_progress": 4,
    "waiting": 1,
    "failed": 0
  }
}
```

**Status Query**:
```bash
# Query status
.automation/scripts/status.sh

# Output:
# MCP Migration Status
# ==================
# ✅ Fix 1 (Service Prefixes)  [COMPLETE] PR #123 merged
# 🔄 Fix 2 (Annotations)       [TESTING] Tests running...
# 🔄 Fix 3 (Error Messages)    [IN PROGRESS] Implementing...
# ⏸️  Fix 4 (Markdown)          [WAITING] Depends on: Fix 1 ✅, Fix 3 🔄
# ✅ Imp 1 (Descriptions)       [COMPLETE] PR #124 merged
# 🔄 Imp 2 (Validation)        [IN PROGRESS] Implementing...
# 🔄 Imp 3 (Truncation)        [IN PROGRESS] Implementing...
#
# Progress: 2/7 complete (28%) | Est. completion: 2h 15m
```

**Real-Time Dashboard** (optional, for interactive mode):
- Use `watch` command to auto-refresh status
- `watch -n 5 .automation/scripts/status.sh`

**Alternatives Considered**:
1. **Log files only**: Rejected - hard to parse, no structured data
2. **Database**: Rejected - overkill, adds complexity
3. **No monitoring**: Rejected - violates user story 4 requirement

**Implementation**:
- Update state file after each status change
- Atomic writes using temp file + mv
- Read-only query doesn't block execution

**References**:
- JSON parsing in bash: https://stedolan.github.io/jq/

---

## Summary of Decisions

| Research Area | Decision | Rationale |
|---------------|----------|-----------|
| **Worktrees** | Isolated worktrees in `/tmp/` with separate branches | Parallel execution, shared `.git` dir, easy cleanup |
| **Dependencies** | DAG with topological sort | Ensures correct execution order, handles Fix 4 dependencies |
| **Testing** | Three-tier: unit + MCP Inspector + integration | Independent validation, protocol compliance, e2e coverage |
| **PR Automation** | `gh pr create` with auto-merge | Already a dependency, supports auto-merge, templated descriptions |
| **Rollback** | Tag-based checkpoint with automated reset | Immutable snapshot, fast recovery, preserves debugging artifacts |
| **Monitoring** | JSON state file + terminal dashboard | Structured data, query without interruption, human-readable status |

## Technologies Confirmed

- **Git**: 2.35+ for worktree support
- **GitHub CLI**: For PR automation (`gh pr create`, `gh pr merge`)
- **jq**: For JSON parsing in bash
- **pytest**: For unit testing
- **MCP Inspector**: For protocol validation (`npx @modelcontextprotocol/inspector`)
- **bash**: 4.0+ for orchestration scripts

## Next Steps

Proceed to **Phase 1: Design & Contracts**

1. Create `data-model.md` (worktree state, dependency graph, fix metadata)
2. Generate contracts (JSON schemas for state tracking)
3. Create `quickstart.md` (how to run the automation)
4. Update agent context with new technologies
