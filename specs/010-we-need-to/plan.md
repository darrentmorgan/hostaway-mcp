# Implementation Plan: Automated Parallel MCP Migration

**Branch**: `010-we-need-to` | **Date**: 2025-10-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-we-need-to/spec.md`

**Note**: This plan outlines the automated parallel execution of the MCP Migration Guide using git worktrees.

## Summary

This feature implements a fully automated, unattended execution system for the 7 MCP improvements defined in `docs/MCP_MIGRATION_GUIDE.md`. The system uses git worktrees to parallelize development across isolated environments, reducing the 12-16 hour sequential migration to approximately 4 hours of wall-clock time. The automation handles worktree creation, dependency-aware task execution, automated testing, PR creation, sequential merging, and rollback capabilities - all without requiring manual intervention.

## Technical Context

**Language/Version**: Python 3.12+ (existing project requirement), Bash 4.0+ for worktree orchestration
**Primary Dependencies**:
- Git 2.35+ (worktree support with enhanced features)
- GitHub CLI (`gh`) for PR automation
- uv package manager for Python dependency isolation
- pytest + httpx_mock for testing
- MCP Inspector (`npx @modelcontextprotocol/inspector`) for validation
**Storage**: Filesystem-based (git worktrees in `/tmp/hostaway-mcp-worktrees/`, logs in `.automation/logs/`)
**Testing**: pytest for each fix validation, MCP Inspector for protocol compliance, integration tests for merged state
**Target Platform**: macOS/Linux development environment (Darwin 24.6.0 per project env)
**Project Type**: Single project with automation scripts
**Performance Goals**:
- Complete all 7 fixes within 4 hours of unattended execution (67-75% faster than 12-16 hour sequential)
- Each worktree completes its fix in 1.5-2 hours average
- Test suite per fix completes in <2 minutes
- PR creation and CI checks complete in <10 minutes per fix
**Constraints**:
- Must execute without user input (fully automated)
- Total disk space for 7 worktrees: <2GB
- Must handle dependency ordering (Fix 4 depends on Fix 1 and Fix 3)
- Must maintain test coverage >80% throughout
- Must preserve main branch stability (no direct commits)
**Scale/Scope**:
- 7 parallel worktrees
- 1 target file (`mcp_stdio_server.py`, ~217 lines → ~400 lines after migration)
- 7 MCP tools affected
- ~183 lines of code added total across all fixes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: API-First Design
**Status**: ✅ **PASS** - Not Applicable (automation tooling, not API endpoints)
**Rationale**: This feature implements automation scripts for parallel development, not FastAPI endpoints or MCP tools. The migration itself adds MCP-compliant features to existing tools, which already follow API-first design.

### Principle II: Type Safety (NON-NEGOTIABLE)
**Status**: ✅ **PASS**
**Compliance**:
- All Python automation scripts will have type annotations
- Bash scripts will use strict error handling (`set -euo pipefail`)
- Worktree state tracking will use typed data structures
- All code changes to `mcp_stdio_server.py` maintain existing mypy --strict compliance
**Verification**: Pre-commit hooks will run mypy on all Python code before commits

### Principle III: Security by Default
**Status**: ✅ **PASS**
**Compliance**:
- GitHub API key read from environment (GH_TOKEN or from `gh auth status`)
- No hardcoded credentials in automation scripts
- Worktrees created in secure temp directories with restricted permissions
- All git operations use authenticated GitHub CLI
- Logs scrubbed of sensitive information before writing
**Note**: The migration adds improved error handling to MCP tools, enhancing security posture

### Principle IV: Test-Driven Development
**Status**: ✅ **PASS**
**Compliance**:
- Each fix has independent test suite defined in migration guide
- Automated testing runs after implementation in each worktree
- Coverage validation ensures >80% threshold maintained
- Integration tests run after all fixes merged
- MCP Inspector validates protocol compliance for each fix
**Test Strategy**: Defined in `research.md` Phase 0 output

### Principle V: Async Performance
**Status**: ✅ **PASS** - Not Applicable (automation tooling)
**Rationale**: Automation scripts use process-level parallelism (git worktrees) rather than async I/O. The MCP server code being modified maintains existing async design (all endpoint functions remain `async def`).

### Overall Constitution Compliance
**Result**: ✅ **APPROVED** - All applicable principles satisfied

**Key Observations**:
1. This is infrastructure/tooling, not application code - API-First and Async principles are N/A
2. Type Safety, Security, and TDD principles are fully satisfied
3. The migration improves MCP tool security and error handling
4. No constitution violations require justification

## Project Structure

### Documentation (this feature)

```
specs/010-we-need-to/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (current)
├── research.md          # Phase 0 output (to be generated)
├── data-model.md        # Phase 1 output (to be generated)
├── quickstart.md        # Phase 1 output (to be generated)
├── contracts/           # Phase 1 output (worktree state schemas)
│   ├── worktree-state.json      # Execution context schema
│   ├── dependency-graph.json    # Fix dependency relationships
│   └── fix-metadata.json        # Fix specifications from migration guide
└── tasks.md             # Phase 2 output (/speckit.tasks - not yet created)
```

### Automation Infrastructure (repository root)

```
.automation/
├── scripts/
│   ├── orchestrator.sh          # Main entry point for parallel execution
│   ├── worktree-manager.sh      # Git worktree CRUD operations
│   ├── fix-executor.sh          # Executes single fix in worktree
│   ├── dependency-resolver.sh   # Resolves fix execution order
│   ├── test-runner.sh           # Runs pytest + MCP Inspector per fix
│   ├── pr-automation.sh         # Creates/merges PRs with gh CLI
│   └── rollback.sh              # Emergency rollback mechanism
├── templates/
│   ├── fix-implementation.py.j2 # Python template for fix implementation
│   └── test-suite.py.j2         # Test template per fix
├── config/
│   ├── dependency-graph.yaml    # Fix 1 → Fix 4, Fix 3 → Fix 4
│   ├── fix-definitions.yaml     # Parsed from migration guide
│   └── worktree-config.yaml     # Worktree paths, branches, timeouts
└── logs/
    ├── orchestrator.log         # Main execution log
    ├── worktree-{fix-name}.log  # Per-worktree logs
    └── test-results/            # Test outputs per fix

/tmp/hostaway-mcp-worktrees/     # Temporary worktree locations
├── fix-1-service-prefixes/
├── fix-2-tool-annotations/
├── fix-3-error-messages/
├── fix-4-markdown-support/
├── imp-1-tool-descriptions/
├── imp-2-input-validation/
└── imp-3-character-limit/

mcp_stdio_server.py              # Target file (217 → ~400 lines)
docs/MCP_MIGRATION_GUIDE.md      # Source of truth for fixes
tests/
├── automation/                   # New tests for automation system
│   ├── test_orchestrator.py
│   ├── test_worktree_manager.py
│   └── test_dependency_resolver.py
└── mcp/                          # Existing MCP tests (will be extended)
    └── test_mcp_stdio_improvements.py  # New test file per migration guide
```

**Structure Decision**: Single project with new `.automation/` directory for orchestration scripts. Worktrees created in `/tmp/` to avoid cluttering repo. All automation is bash-based for portability, with Python used only for fix implementation within worktrees (leveraging existing project environment).

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: ✅ **No Violations** - Complexity tracking not required

All constitution principles are satisfied. No violations to justify.
