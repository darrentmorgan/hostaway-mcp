# Tasks: Automated Parallel MCP Migration

**Input**: Design documents from `/specs/010-we-need-to/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/
**Branch**: `010-we-need-to`
**Feature**: Automated execution of MCP Migration Guide using parallel git worktrees

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story this task belongs to (US1, US2, US3, US4)
- File paths are absolute

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic directory structure

- [X] T001 Create `.automation/` directory structure with subdirectories (scripts/, templates/, config/, logs/)
- [X] T002 [P] Create `.automation/logs/` with .gitkeep (logs are gitignored but directory tracked)
- [X] T003 [P] Add `.automation/logs/*` to `.gitignore` but preserve directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `.automation/config/dependency-graph.yaml` defining fix relationships (Fix 1 → Fix 4, Fix 3 → Fix 4)
- [X] T005 [P] Create `.automation/config/fix-definitions.yaml` with all 7 fix specifications from data-model.md
- [X] T006 [P] Create `.automation/config/worktree-config.yaml` with worktree paths, timeouts, cleanup settings
- [X] T007 Create `.automation/templates/pr-body.md` template for GitHub PR descriptions (implemented inline in pr-automation.sh)
- [X] T008 [P] Create `.automation/scripts/validate-state.sh` for state file integrity checks (implemented as validate-config.sh)
- [X] T009 [P] Create `tests/automation/__init__.py` for test package initialization

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Parallel Development (Priority: P1) 🎯 MVP

**Goal**: Fully automated execution of all 7 MCP fixes in parallel using git worktrees without manual intervention

**Independent Test**: Run `.automation/scripts/orchestrator.sh` and verify all 7 worktrees are created, fixes implemented, tests pass, PRs created and merged automatically

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Create `tests/automation/test_worktree_manager.py` with tests for worktree CRUD operations
- [X] T011 [P] [US1] Create `tests/automation/test_fix_executor.py` with tests for single fix execution in worktree
- [X] T012 [P] [US1] Create `tests/automation/test_orchestrator.py` with tests for parallel execution coordination

### Implementation for User Story 1

#### Worktree Management (Core)

- [X] T013 [US1] Create `.automation/scripts/worktree-manager.sh` with functions:
  - `create_worktree(fix_id, branch_name)`: Create isolated worktree in `/tmp/`
  - `remove_worktree(fix_id)`: Clean up worktree and branch
  - `list_worktrees()`: List all active MCP migration worktrees
  - Error handling: worktree already exists, insufficient disk space
  - Include `set -euo pipefail` for strict error handling

#### Fix Execution (Core)

- [X] T014 [US1] Create `.automation/scripts/fix-executor.sh` to execute single fix in worktree:
  - Parse `fix-definitions.yaml` to get fix implementation details
  - Extract code from `docs/MCP_MIGRATION_GUIDE.md` for this fix
  - Apply fix to `mcp_stdio_server.py` in worktree
  - Update execution state in `.automation/logs/execution-state.json`
  - Log to `.automation/logs/worktree-{fix-name}.log`
  - Handle timeouts (default: 7200 seconds per fix)

#### Orchestration (Core)

- [X] T015 [US1] Create `.automation/scripts/orchestrator.sh` main entry point:
  - Parse command-line arguments (--dry-run, --fixes, --debug, --help)
  - Create pre-migration checkpoint tag with timestamp
  - Initialize execution state JSON file
  - Read `dependency-graph.yaml` and compute execution waves
  - Launch fix-executor.sh for each fix in Wave 1 as background processes
  - Monitor completion using state file
  - Trigger Wave 2 (Fix 4) once dependencies (Fix 1, Fix 3) complete
  - Handle parallel execution errors (continue others if one fails)
  - Generate summary report on completion

#### Testing Automation

- [X] T016 [US1] Create `.automation/scripts/test-runner.sh` to run tests per fix:
  - Execute `uv run pytest tests/automation/test_fix_{n}.py` for unit tests
  - Execute `npx @modelcontextprotocol/inspector mcp_stdio_server.py` for MCP validation
  - Parse test results and update state file
  - Retry once on failure, then mark as failed
  - Verify coverage threshold >80% maintained
  - Return exit code 0 for pass, 1 for fail

#### PR Automation

- [X] T017 [US1] Create `.automation/scripts/pr-automation.sh` for GitHub operations:
  - Function `create_pr(fix_id, branch_name)`: Use `gh pr create` with template
  - Function `enable_auto_merge(pr_number)`: Use `gh pr merge --auto --squash`
  - Function `get_pr_status(pr_number)`: Check CI status
  - Function `list_open_prs()`: List PRs with mcp-migration label
  - Handle rate limiting (GitHub API: 5000 req/hr authenticated)
  - Generate PR title following conventional commits format

#### State Management

- [X] T018 [P] [US1] Create Python helper `.automation/scripts/state_manager.py` for JSON state operations:
  - `read_state()`: Parse `.automation/logs/execution-state.json`
  - `update_worktree_status(fix_id, status)`: Atomic write using temp file
  - `get_completion_status()`: Return summary (completed, failed, in_progress, waiting)
  - Type annotations using data model from `contracts/worktree-state.json`
  - Validation against JSON schemas

#### Status Monitoring

- [X] T019 [P] [US1] Create `.automation/scripts/status.sh` for real-time progress query:
  - Read execution state JSON
  - Format terminal-friendly output with emoji indicators (✅, 🔄, ⏸️, ❌)
  - Show dependencies and blocking status
  - Calculate estimated completion time based on remaining fixes
  - Support --json flag for programmatic access

**Checkpoint**: At this point, User Story 1 (core automation) should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dependency-Aware Sequencing (Priority: P2)

**Goal**: Ensure Fix 4 (Markdown) correctly uses renamed tool names from Fix 1 and error helpers from Fix 3

**Independent Test**: Run orchestrator and verify Fix 4 waits for Fix 1 and Fix 3, then uses `hostaway_list_properties` (not `list_properties`) and error helper functions

### Implementation for User Story 2

- [X] T020 [US2] Create `.automation/scripts/dependency-resolver.sh`:
  - Function `parse_dependency_graph(yaml_file)`: Load YAML, build adjacency list
  - Function `topological_sort(graph)`: Kahn's algorithm for execution order
  - Function `check_dependencies_met(fix_id, state)`: Verify all deps complete
  - Function `get_execution_wave(wave_number)`: Return fixes for parallel execution
  - Handle circular dependency detection (error out if cycle found)
  - **IMPLEMENTED INLINE** in orchestrator.sh as `load_execution_order()` function

- [X] T021 [US2] Update `.automation/scripts/orchestrator.sh` to use dependency resolver:
  - Call `dependency-resolver.sh` to get execution waves
  - Launch fixes within same wave in parallel
  - Wait for wave completion before starting next wave
  - Update state file with dependency status per fix
  - **COMPLETE** orchestrator.sh executes waves sequentially with parallel fixes per wave

- [X] T022 [US2] Update `.automation/scripts/fix-executor.sh` to handle dependencies:
  - Before starting, check dependencies met using dependency-resolver
  - If dependencies not met, set status to `waiting_dependencies`
  - Poll state file every 30 seconds until dependencies complete
  - Once met, proceed with implementation
  - **COMPLETE** Wave-based execution handles dependencies at orchestrator level

- [X] T023 [P] [US2] Create test `tests/automation/test_dependency_resolver.py`:
  - Test topological sort with sample DAG
  - Test cycle detection (should error)
  - Test execution wave grouping
  - Test dependency checking logic

**Checkpoint**: Dependency-aware execution verified - Fix 4 correctly waits and uses updated code from Fix 1 and Fix 3

---

## Phase 5: User Story 3 - Comprehensive Test Coverage (Priority: P2)

**Goal**: Each fix has independent test suite that validates implementation without requiring other fixes

**Independent Test**: Run test suite for Fix 1 in isolation and verify it validates service prefixes without needing other fixes

### Implementation for User Story 3

- [ ] T024 [US3] Create `tests/mcp/test_mcp_stdio_improvements.py` with test functions per fix:
  - `test_fix_1_service_prefixes()`: Verify all 7 tools have `hostaway_` prefix
  - `test_fix_2_tool_annotations()`: Verify annotations present (readOnlyHint, etc.)
  - `test_fix_3_error_messages()`: Test actionable error responses
  - `test_fix_4_markdown_formatting()`: Test JSON and Markdown formats
  - `test_imp_1_tool_descriptions()`: Verify enhanced descriptions
  - `test_imp_2_input_validation()`: Test input constraints
  - `test_imp_3_character_limit()`: Test truncation at 25000 chars

- [ ] T025 [US3] Create `.automation/templates/test-suite.py.j2` Jinja2 template:
  - Template for generating test files per fix
  - Parameterized by fix_id, expected_changes, test_scenarios
  - Used by fix-executor.sh to generate tests dynamically

- [ ] T026 [US3] Update `.automation/scripts/test-runner.sh` to run MCP Inspector:
  - Add function `run_mcp_inspector(worktree_path)`
  - Execute: `npx @modelcontextprotocol/inspector mcp_stdio_server.py --validate-tools`
  - Parse output for PASS/FAIL status
  - Check for protocol compliance violations
  - Update test_results in state file

- [ ] T027 [US3] Create integration test `tests/mcp/test_integration_all_fixes.py`:
  - Run only AFTER all 7 fixes merged
  - Test all 7 end-to-end scenarios from migration guide
  - Test cases: list properties, get details, check availability, error handling, etc.
  - Verify MCP Inspector reports 10/10 compliance

**Checkpoint**: Comprehensive testing infrastructure in place - each fix validated independently

---

## Phase 6: User Story 4 - Progress Monitoring and Rollback (Priority: P3)

**Goal**: Real-time visibility into parallel execution status and ability to rollback on failure

**Independent Test**: Simulate critical failure and verify rollback restores to pre-migration state within 5 minutes

### Implementation for User Story 4

#### Progress Monitoring

- [ ] T028 [P] [US4] Update `.automation/scripts/status.sh` with advanced features:
  - Add `--watch` mode (auto-refresh every 5 seconds)
  - Add metrics display (time saved, parallelization efficiency)
  - Add estimated completion time based on average fix duration
  - Color-coded output (green=complete, yellow=in progress, red=failed)

- [ ] T029 [P] [US4] Create `.automation/scripts/generate-report.sh`:
  - Parse execution state JSON when migration completes
  - Generate summary markdown report in `.automation/logs/summary-report.md`
  - Include: total duration, time saved, test results, PR numbers
  - Calculate parallelization efficiency: (sequential_time - actual_time) / sequential_time

#### Rollback Mechanism

- [ ] T030 [US4] Create `.automation/scripts/rollback.sh` for emergency recovery:
  - Function `create_checkpoint()`: Tag current state with timestamp
  - Function `stop_all_worktrees()`: Kill all fix-executor processes
  - Function `remove_all_branches()`: Delete all `mcp-fix-*` branches
  - Function `reset_main_branch(tag)`: Hard reset to checkpoint tag
  - Function `close_all_prs()`: Close PRs with mcp-migration label
  - Function `cleanup_worktrees()`: Remove /tmp/hostaway-mcp-worktrees/
  - Log all rollback actions to `.automation/logs/rollback-{timestamp}.log`

- [ ] T031 [US4] Update `.automation/scripts/orchestrator.sh` to support rollback:
  - Add `--rollback` flag to trigger emergency rollback
  - Call `rollback.sh` if 3+ fixes fail tests (failure threshold)
  - Preserve logs and state file before rollback for debugging
  - Update state to `rolled_back` status

- [ ] T032 [P] [US4] Create test `tests/automation/test_rollback.py`:
  - Test checkpoint creation and tagging
  - Test worktree cleanup
  - Test branch deletion
  - Test PR closing
  - Mock git operations for safety

#### Final Validation

- [ ] T033 [P] [US4] Create `.automation/scripts/validate-migration.sh`:
  - Run after all PRs merged
  - Execute full test suite: `pytest tests/mcp/`
  - Run MCP Inspector on final `mcp_stdio_server.py`
  - Verify coverage threshold maintained
  - Check for regression in existing tests
  - Output validation report

**Checkpoint**: Monitoring and rollback capabilities complete - production-safe automation

---

## Phase 7: Polish & Integration

**Purpose**: Cross-cutting concerns, documentation, and final integration

- [ ] T034 [P] Create quickstart documentation `.automation/README.md`:
  - How to run the orchestrator
  - Configuration options
  - Troubleshooting guide
  - FAQ section

- [ ] T035 [P] Add error handling and logging to all scripts:
  - Ensure all scripts use `set -euo pipefail`
  - Add trap handlers for cleanup on script exit
  - Standardize log format: `[TIMESTAMP] [LEVEL] [SCRIPT] Message`

- [ ] T036 [P] Create `.automation/scripts/cleanup.sh` for manual cleanup:
  - Remove stale worktrees
  - Clean up old logs (keep last 10 runs)
  - Prune git worktrees
  - Validate no orphaned branches

- [ ] T037 Update project README.md with automation section:
  - Add "Automated MCP Migration" section
  - Link to `.automation/README.md`
  - Add quick start command
  - Document prerequisites

- [ ] T038 [P] Create `.automation/.dockerignore` if automation needs containerization (future)

- [ ] T039 [P] Run final integration test of complete workflow:
  - Execute orchestrator.sh on clean branch
  - Verify all 7 fixes complete
  - Verify PRs created and merged
  - Verify final MCP compliance
  - Verify cleanup completes successfully

---

## Dependency Graph

```
Phase 1 (Setup) → Phase 2 (Foundation)
                       ↓
                  Phase 3 (US1: Automation Core)
                       ↓
         ┌─────────────┴─────────────┬──────────────┐
         ↓                           ↓              ↓
    Phase 4 (US2: Dependencies)  Phase 5 (US3: Tests)  Phase 6 (US4: Monitoring)
         ↓                           ↓              ↓
         └─────────────┬─────────────┴──────────────┘
                       ↓
                  Phase 7 (Polish)
```

**Story Completion Order**:
1. User Story 1 (P1) - **MVP**: Core automation (T013-T019)
2. User Story 2 (P2) - Dependency resolution (T020-T023)
3. User Story 3 (P2) - Test coverage (T024-T027) [can run parallel with US2]
4. User Story 4 (P3) - Monitoring and rollback (T028-T033)

---

## Parallel Execution Examples

### Phase 2 (Foundation) - 6 parallel tasks
```bash
# All config files can be created in parallel
T004 & T005 & T006 & T007 & T008 & T009 &
wait
```

### Phase 3 (US1) - Multiple parallel opportunities
```bash
# Tests can be written in parallel
T010 & T011 & T012 &
wait

# State manager and status script are independent
T018 & T019 &
wait
```

### Phases 4-6 (US2-US4) - Can execute stories in parallel
```bash
# User Story 2, 3, 4 can work on different files simultaneously
# US2: dependency-resolver.sh
# US3: test files
# US4: rollback.sh, status.sh enhancements
```

---

## Implementation Strategy

**MVP Scope** (User Story 1 only):
- Tasks T001-T019 (19 tasks)
- Delivers: Fully functional automated parallel execution
- Estimated time: 8-12 hours
- Milestone: Can execute migration guide automatically

**Full Feature** (All 4 User Stories):
- Tasks T001-T039 (39 tasks)
- Estimated time: 16-20 hours total
- Incremental delivery: Each story adds value independently

---

## Testing Checkpoints

After each phase, run validation:

**Phase 1-2**: Verify directory structure and config files exist
```bash
test -d .automation/scripts && test -f .automation/config/dependency-graph.yaml
```

**Phase 3** (US1 MVP): End-to-end smoke test
```bash
.automation/scripts/orchestrator.sh --dry-run
# Should show 7 worktrees would be created, no errors
```

**Phase 4** (US2): Dependency resolution test
```bash
.automation/scripts/dependency-resolver.sh
# Should output: Wave 1: [6 fixes], Wave 2: [fix-4]
```

**Phase 5** (US3): Test suite validation
```bash
uv run pytest tests/mcp/test_mcp_stdio_improvements.py -v
# All tests should fail initially (TDD), pass after fixes applied
```

**Phase 6** (US4): Rollback test
```bash
.automation/scripts/rollback.sh --dry-run
# Should show rollback steps without executing
```

**Phase 7**: Full integration
```bash
.automation/scripts/orchestrator.sh
# Complete end-to-end execution, verify all PRs merged
```

---

## Success Criteria Mapping

- **SC-001** (4 hour execution): Achieved by Phase 3 (US1) - parallel worktrees
- **SC-002** (100% test pass): Achieved by Phase 5 (US3) - comprehensive tests
- **SC-003** (zero manual intervention): Achieved by Phase 3 (US1) - full automation
- **SC-004** (10/10 MCP compliance): Achieved by Phase 5 (US3) - MCP Inspector validation
- **SC-005** (E2E test pass): Achieved by Phase 5 (US3) - integration tests
- **SC-006** (60%+ time savings): Achieved by Phase 3 (US1) - parallel execution
- **SC-007** (merge conflict handling): Achieved by Phase 4 (US2) - sequential merging
- **SC-008** (5 min rollback): Achieved by Phase 6 (US4) - rollback.sh

---

## Total Task Count: 39 tasks

**By User Story**:
- Setup & Foundation: 9 tasks (T001-T009)
- User Story 1 (P1): 10 tasks (T010-T019) ← **MVP**
- User Story 2 (P2): 4 tasks (T020-T023)
- User Story 3 (P2): 4 tasks (T024-T027)
- User Story 4 (P3): 6 tasks (T028-T033)
- Polish & Integration: 6 tasks (T034-T039)

**Parallel Opportunities**: 15 tasks marked [P] can run concurrently
**Sequential Dependencies**: Clear checkpoint markers after each user story
**Independent Testing**: Each story has acceptance criteria and can be validated independently
