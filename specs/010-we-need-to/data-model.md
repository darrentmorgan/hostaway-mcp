# Data Model: Automated Parallel MCP Migration

**Feature**: 010-we-need-to | **Date**: 2025-10-30
**Phase**: 1 - Design & Contracts

## Entity Definitions

### Entity 1: Worktree

**Purpose**: Represents an isolated git working directory for implementing a single fix

**Attributes**:
- `fix_id` (string): Unique identifier (e.g., "fix-1-service-prefixes")
- `branch_name` (string): Git branch name (e.g., "mcp-fix-1-service-prefixes")
- `worktree_path` (string): Absolute filesystem path (e.g., "/tmp/hostaway-mcp-worktrees/fix-1-service-prefixes")
- `status` (enum): Current execution state
  - `not_started`: Worktree created but execution not begun
  - `implementing`: Applying fix from migration guide
  - `testing`: Running pytest + MCP Inspector
  - `pr_created`: PR opened, waiting for CI
  - `complete`: PR merged, worktree can be cleaned up
  - `failed`: Tests or implementation failed
  - `waiting_dependencies`: Blocked by unmet dependencies
- `dependencies` (array[string]): List of fix_ids that must complete first
- `start_time` (ISO8601 timestamp): When implementation began
- `end_time` (ISO8601 timestamp): When worktree reached terminal state (complete/failed)
- `pr_number` (integer, nullable): GitHub PR number if created
- `test_results` (object):
  - `unit_tests_pass` (boolean)
  - `mcp_inspector_pass` (boolean)
  - `coverage_percent` (float)
- `error_log_path` (string, nullable): Path to error log if failed

**Relationships**:
- Worktree ↔ Fix (one-to-one)
- Worktree → Worktree (many dependencies)

**State Transitions**:
```
not_started → implementing → testing → pr_created → complete
     ↓            ↓            ↓           ↓
   failed ←─────┴────────────┴───────────┘

not_started → waiting_dependencies → implementing
     ↓                   ↓
   failed ←─────────────┘
```

**Validation Rules**:
- `fix_id` must match pattern: `(fix|imp)-\d+-[a-z-]+`
- `worktree_path` must be absolute path under `/tmp/hostaway-mcp-worktrees/`
- `branch_name` must start with `mcp-`
- `dependencies` must reference valid fix_ids
- `status` must follow state machine transitions
- `end_time` must be after `start_time` when present

---

### Entity 2: Fix

**Purpose**: Represents a discrete MCP improvement from the migration guide

**Attributes**:
- `fix_id` (string): Unique identifier
- `fix_number` (integer): Ordering number (1-7)
- `fix_type` (enum): `high_priority` or `medium_priority`
- `name` (string): Human-readable name (e.g., "Service Prefixes")
- `description` (string): Brief description of what the fix does
- `migration_guide_section` (string): Section reference in guide (e.g., "Fix 1: Add Service Prefixes")
- `estimated_duration_seconds` (integer): Expected time to implement (1.5-2 hours = 5400-7200 sec)
- `target_file` (string): File to modify (always "mcp_stdio_server.py" for this migration)
- `lines_added` (integer): Approximate lines of code added
- `test_file` (string): Test file path (e.g., "tests/mcp/test_service_prefixes.py")
- `dependencies` (array[string]): Fix IDs that must complete first

**Relationships**:
- Fix ↔ Worktree (one-to-one during execution)
- Fix → Fix (many dependencies via dependency graph)

**Fix Catalog** (from migration guide):
```yaml
fixes:
  - fix_id: "fix-1-service-prefixes"
    fix_number: 1
    fix_type: "high_priority"
    name: "Service Prefixes"
    estimated_duration_seconds: 5400  # 1.5 hours
    lines_added: 14  # 7 tool name changes + 7 routing logic updates
    dependencies: []

  - fix_id: "fix-2-tool-annotations"
    fix_number: 2
    fix_type: "high_priority"
    name: "Tool Annotations"
    estimated_duration_seconds: 1800  # 30 minutes
    lines_added: 56  # 8 lines × 7 tools
    dependencies: []

  - fix_id: "fix-3-error-messages"
    fix_number: 3
    fix_type: "high_priority"
    name: "Error Messages"
    estimated_duration_seconds: 9000  # 2.5 hours
    lines_added: 60  # 2 helper functions + validation in 7 tools
    dependencies: []

  - fix_id: "fix-4-markdown-support"
    fix_number: 4
    fix_type: "high_priority"
    name: "Markdown Support"
    estimated_duration_seconds: 12600  # 3.5 hours
    lines_added: 237  # 6 formatter functions + response_format param
    dependencies: ["fix-1-service-prefixes", "fix-3-error-messages"]

  - fix_id: "imp-1-tool-descriptions"
    fix_number: 5
    fix_type: "medium_priority"
    name: "Enhanced Tool Descriptions"
    estimated_duration_seconds: 9000  # 2.5 hours
    lines_added: 105  # 15 lines × 7 tools
    dependencies: []

  - fix_id: "imp-2-input-validation"
    fix_number: 6
    fix_type: "medium_priority"
    name: "Input Validation"
    estimated_duration_seconds: 9000  # 2.5 hours
    lines_added: 42  # 6 lines × 7 tools
    dependencies: []

  - fix_id: "imp-3-character-limit"
    fix_number: 7
    fix_type: "medium_priority"
    name: "CHARACTER_LIMIT Truncation"
    estimated_duration_seconds: 5400  # 1.5 hours
    lines_added: 32  # 1 constant + 1 function + 7 tool call sites
    dependencies: []
```

**Validation Rules**:
- `fix_id` must be unique across all fixes
- `fix_number` must be sequential 1-7
- `dependencies` must not create cycles (must be a DAG)
- `estimated_duration_seconds` must be positive
- `target_file` must exist in repository

---

### Entity 3: Dependency Graph

**Purpose**: Defines execution order and dependency relationships between fixes

**Attributes**:
- `nodes` (array[string]): List of all fix_ids
- `edges` (array[object]): Directed edges representing dependencies
  - `from` (string): Fix ID that must complete first
  - `to` (string): Fix ID that depends on `from`
- `execution_order` (array[string]): Topologically sorted list of fix_ids

**Graph Structure**:
```
Nodes: [fix-1, fix-2, fix-3, fix-4, imp-1, imp-2, imp-3]

Edges:
  fix-1 → fix-4
  fix-3 → fix-4

Execution Order (topological sort):
  Wave 1 (parallel): [fix-1, fix-2, fix-3, imp-1, imp-2, imp-3]
  Wave 2 (after fix-1 and fix-3): [fix-4]
```

**Validation Rules**:
- Graph must be acyclic (no circular dependencies)
- All edges must reference valid fix_ids
- `execution_order` must satisfy dependency constraints
- Orphaned nodes (no edges) can execute immediately

**Dependency Resolution Algorithm**:
1. Parse dependency edges from fix catalog
2. Build adjacency list representation
3. Perform topological sort (Kahn's algorithm)
4. Group into execution waves (fixes with no pending dependencies)
5. Execute wave in parallel, wait for wave completion before next wave

---

### Entity 4: Execution Context

**Purpose**: Tracks overall migration execution state and metrics

**Attributes**:
- `execution_id` (string): Unique run identifier (e.g., "mcp-migration-20251030-143022")
- `start_time` (ISO8601 timestamp): When orchestrator started
- `end_time` (ISO8601 timestamp, nullable): When all fixes complete or failed
- `status` (enum):
  - `initializing`: Creating worktrees and branches
  - `executing`: One or more fixes in progress
  - `merging`: PRs being merged sequentially
  - `validating`: Running final integration tests
  - `complete`: All fixes merged successfully
  - `failed`: One or more critical failures
  - `rolled_back`: Migration rolled back to checkpoint
- `checkpoint_tag` (string): Git tag for rollback point (e.g., "pre-mcp-migration-20251030-143022")
- `worktrees` (object): Map of fix_id → Worktree entity
- `summary` (object):
  - `total_fixes` (integer): 7
  - `completed` (integer): Number of fixes successfully merged
  - `failed` (integer): Number of fixes that failed
  - `in_progress` (integer): Number of fixes currently executing
  - `waiting` (integer): Number of fixes blocked by dependencies
- `metrics` (object):
  - `total_duration_seconds` (integer): Wall-clock time from start to end
  - `sequential_duration_estimate_seconds` (integer): 43200-57600 (12-16 hours)
  - `time_saved_percent` (float): (sequential - actual) / sequential × 100
  - `parallelization_efficiency` (float): Actual improvement vs theoretical max

**Relationships**:
- ExecutionContext → Worktree (one-to-many)
- ExecutionContext → DependencyGraph (one-to-one)

**Validation Rules**:
- `execution_id` must be unique per run
- `status` must follow state machine
- `summary.total_fixes` must equal 7
- `summary` counts must sum to `total_fixes`
- `end_time` must be after `start_time` when present

**State Transitions**:
```
initializing → executing → merging → validating → complete
     ↓             ↓           ↓          ↓
   failed ←───────┴───────────┴──────────┘
     ↓
rolled_back
```

---

## Data Storage

**State File**: `.automation/logs/execution-state.json`
**Format**: JSON (for easy parsing in bash with `jq`)
**Access Pattern**:
- Write: Orchestrator and worker scripts (atomic writes via temp file)
- Read: Status query script (read-only, non-blocking)

**Example State File**:
```json
{
  "execution_id": "mcp-migration-20251030-143022",
  "start_time": "2025-10-30T14:30:22Z",
  "end_time": null,
  "status": "executing",
  "checkpoint_tag": "pre-mcp-migration-20251030-143022",
  "worktrees": {
    "fix-1-service-prefixes": {
      "fix_id": "fix-1-service-prefixes",
      "branch_name": "mcp-fix-1-service-prefixes",
      "worktree_path": "/tmp/hostaway-mcp-worktrees/fix-1-service-prefixes",
      "status": "complete",
      "dependencies": [],
      "start_time": "2025-10-30T14:30:25Z",
      "end_time": "2025-10-30T15:45:12Z",
      "pr_number": 123,
      "test_results": {
        "unit_tests_pass": true,
        "mcp_inspector_pass": true,
        "coverage_percent": 82.5
      },
      "error_log_path": null
    },
    "fix-4-markdown-support": {
      "fix_id": "fix-4-markdown-support",
      "branch_name": "mcp-fix-4-markdown-support",
      "worktree_path": "/tmp/hostaway-mcp-worktrees/fix-4-markdown-support",
      "status": "waiting_dependencies",
      "dependencies": ["fix-1-service-prefixes", "fix-3-error-messages"],
      "start_time": null,
      "end_time": null,
      "pr_number": null,
      "test_results": {},
      "error_log_path": null
    }
  },
  "summary": {
    "total_fixes": 7,
    "completed": 2,
    "failed": 0,
    "in_progress": 4,
    "waiting": 1
  },
  "metrics": {
    "total_duration_seconds": null,
    "sequential_duration_estimate_seconds": 50400,
    "time_saved_percent": null,
    "parallelization_efficiency": null
  }
}
```

---

## Relationships Diagram

```
ExecutionContext
  ├── has_many: Worktree (7 worktrees)
  ├── has_one: DependencyGraph
  └── tracks: ExecutionMetrics

Worktree
  ├── implements: Fix (one-to-one)
  ├── depends_on: Worktree[] (via dependency graph)
  └── produces: TestResults

Fix
  ├── defines: Dependencies (to other fixes)
  ├── specifies: ImplementationDetails
  └── tested_by: TestSuite

DependencyGraph
  ├── contains: Node[] (fix_ids)
  ├── defines: Edge[] (dependencies)
  └── computes: ExecutionOrder (topological sort)
```

---

## Validation & Integrity

**Invariants**:
1. Sum of worktree statuses must equal total_fixes
2. Dependency graph must be acyclic
3. A worktree can only transition to `implementing` if all dependencies are `complete`
4. Test results must be populated when status is `pr_created` or `complete`
5. `end_time` must be present when status is terminal (`complete` or `failed`)

**Validation Scripts**:
- `.automation/scripts/validate-state.sh`: Checks state file integrity
- Run after each state update
- Fail-fast on validation errors

---

## Evolution Strategy

**Version 1** (current): JSON-based state file
**Future Enhancements** (out of scope for v1):
- SQLite database for better querying
- Web dashboard for real-time monitoring
- Prometheus metrics export
- Distributed execution across multiple machines
