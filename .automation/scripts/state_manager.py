#!/usr/bin/env python3
"""State Manager for MCP Migration Orchestration

Manages execution state with type-safe data structures.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path


class WorktreeStatus(str, Enum):
    """Worktree execution status."""

    NOT_STARTED = "not_started"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    PR_CREATED = "pr_created"
    COMPLETE = "complete"
    FAILED = "failed"
    WAITING_DEPENDENCIES = "waiting_dependencies"


@dataclass
class TestResults:
    """Test results for a fix."""

    unit_tests_pass: bool = False
    mcp_inspector_pass: bool = False
    coverage_percent: float | None = None


@dataclass
class WorktreeState:
    """State of a single worktree."""

    fix_id: str
    branch_name: str
    worktree_path: str
    status: WorktreeStatus
    dependencies: list[str] = field(default_factory=list)
    start_time: str | None = None
    end_time: str | None = None
    pr_number: int | None = None
    test_results: TestResults | None = None
    error_log_path: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["status"] = self.status.value
        if self.test_results:
            data["test_results"] = asdict(self.test_results)
        return data


@dataclass
class ExecutionState:
    """Overall execution state."""

    execution_id: str
    start_time: str
    status: str
    worktrees: list[WorktreeState] = field(default_factory=list)
    end_time: str | None = None
    checkpoint_tag: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "execution_id": self.execution_id,
            "start_time": self.start_time,
            "status": self.status,
            "worktrees": [wt.to_dict() for wt in self.worktrees],
            "end_time": self.end_time,
            "checkpoint_tag": self.checkpoint_tag,
        }


class StateManager:
    """Manages execution state with atomic file operations."""

    def __init__(self, state_file: Path):
        """Initialize state manager.

        Args:
            state_file: Path to JSON state file
        """
        self.state_file = state_file
        self._state: ExecutionState | None = None

    def initialize(self, checkpoint_tag: str | None = None) -> ExecutionState:
        """Initialize new execution state.

        Args:
            checkpoint_tag: Optional git tag for rollback

        Returns:
            New execution state
        """
        execution_id = f"mcp-migration-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"

        self._state = ExecutionState(
            execution_id=execution_id,
            start_time=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            status="in_progress",
            checkpoint_tag=checkpoint_tag,
        )

        self._save()
        return self._state

    def load(self) -> ExecutionState:
        """Load execution state from file.

        Returns:
            Execution state

        Raises:
            FileNotFoundError: If state file doesn't exist
            ValueError: If state file is invalid
        """
        if not self.state_file.exists():
            raise FileNotFoundError(f"State file not found: {self.state_file}")

        with self.state_file.open() as f:
            data = json.load(f)

        # Reconstruct worktree states
        worktrees = []
        for wt_data in data.get("worktrees", []):
            test_results = None
            if wt_data.get("test_results"):
                test_results = TestResults(**wt_data["test_results"])

            worktree = WorktreeState(
                fix_id=wt_data["fix_id"],
                branch_name=wt_data["branch_name"],
                worktree_path=wt_data["worktree_path"],
                status=WorktreeStatus(wt_data["status"]),
                dependencies=wt_data.get("dependencies", []),
                start_time=wt_data.get("start_time"),
                end_time=wt_data.get("end_time"),
                pr_number=wt_data.get("pr_number"),
                test_results=test_results,
                error_log_path=wt_data.get("error_log_path"),
            )
            worktrees.append(worktree)

        self._state = ExecutionState(
            execution_id=data["execution_id"],
            start_time=data["start_time"],
            status=data["status"],
            worktrees=worktrees,
            end_time=data.get("end_time"),
            checkpoint_tag=data.get("checkpoint_tag"),
        )

        return self._state

    def add_worktree(self, worktree: WorktreeState) -> None:
        """Add a worktree to state.

        Args:
            worktree: Worktree state to add
        """
        if not self._state:
            raise ValueError("State not initialized. Call initialize() first.")

        self._state.worktrees.append(worktree)
        self._save()

    def update_worktree(
        self,
        fix_id: str,
        status: WorktreeStatus | None = None,
        pr_number: int | None = None,
        test_results: TestResults | None = None,
        error_log_path: str | None = None,
    ) -> None:
        """Update a worktree's state.

        Args:
            fix_id: Fix identifier
            status: New status
            pr_number: PR number if created
            test_results: Test results if available
            error_log_path: Path to error log if failed
        """
        if not self._state:
            raise ValueError("State not initialized")

        worktree = next((wt for wt in self._state.worktrees if wt.fix_id == fix_id), None)
        if not worktree:
            raise ValueError(f"Worktree not found: {fix_id}")

        if status:
            worktree.status = status

            # Set start time when moving to implementing
            if status == WorktreeStatus.IMPLEMENTING and not worktree.start_time:
                worktree.start_time = datetime.now(UTC).isoformat().replace("+00:00", "Z")

            # Set end time when reaching terminal state
            if status in (WorktreeStatus.COMPLETE, WorktreeStatus.FAILED):
                worktree.end_time = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        if pr_number:
            worktree.pr_number = pr_number

        if test_results:
            worktree.test_results = test_results

        if error_log_path:
            worktree.error_log_path = error_log_path

        self._save()

    def mark_complete(self) -> None:
        """Mark execution as complete."""
        if not self._state:
            raise ValueError("State not initialized")

        self._state.status = "complete"
        self._state.end_time = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        self._save()

    def mark_failed(self) -> None:
        """Mark execution as failed."""
        if not self._state:
            raise ValueError("State not initialized")

        self._state.status = "failed"
        self._state.end_time = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        self._save()

    def get_worktree(self, fix_id: str) -> WorktreeState | None:
        """Get worktree state by fix_id.

        Args:
            fix_id: Fix identifier

        Returns:
            Worktree state or None if not found
        """
        if not self._state:
            return None

        return next((wt for wt in self._state.worktrees if wt.fix_id == fix_id), None)

    def get_summary(self) -> dict:
        """Get execution summary.

        Returns:
            Summary statistics
        """
        if not self._state:
            return {}

        total = len(self._state.worktrees)
        complete = sum(1 for wt in self._state.worktrees if wt.status == WorktreeStatus.COMPLETE)
        failed = sum(1 for wt in self._state.worktrees if wt.status == WorktreeStatus.FAILED)
        in_progress = sum(
            1
            for wt in self._state.worktrees
            if wt.status in (WorktreeStatus.IMPLEMENTING, WorktreeStatus.TESTING)
        )

        return {
            "execution_id": self._state.execution_id,
            "status": self._state.status,
            "total_fixes": total,
            "complete": complete,
            "failed": failed,
            "in_progress": in_progress,
            "success_rate": (complete / total * 100) if total > 0 else 0,
        }

    def _save(self) -> None:
        """Save state to file atomically."""
        if not self._state:
            raise ValueError("State not initialized")

        # Write to temp file first
        temp_file = self.state_file.with_suffix(".tmp")

        with temp_file.open("w") as f:
            json.dump(self._state.to_dict(), f, indent=2)

        # Atomic rename
        temp_file.replace(self.state_file)


def main():
    """CLI interface for state manager."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: state_manager.py <command> [args]")
        print("Commands:")
        print("  init <state_file>")
        print("  load <state_file>")
        print("  summary <state_file>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        if len(sys.argv) < 3:
            print("Usage: state_manager.py init <state_file>")
            sys.exit(1)

        state_file = Path(sys.argv[2])
        manager = StateManager(state_file)
        state = manager.initialize()

        print(f"Initialized execution: {state.execution_id}")

    elif command == "load":
        if len(sys.argv) < 3:
            print("Usage: state_manager.py load <state_file>")
            sys.exit(1)

        state_file = Path(sys.argv[2])
        manager = StateManager(state_file)

        try:
            state = manager.load()
            print(json.dumps(state.to_dict(), indent=2))
        except FileNotFoundError:
            print(f"ERROR: State file not found: {state_file}")
            sys.exit(1)

    elif command == "summary":
        if len(sys.argv) < 3:
            print("Usage: state_manager.py summary <state_file>")
            sys.exit(1)

        state_file = Path(sys.argv[2])
        manager = StateManager(state_file)

        try:
            manager.load()
            summary = manager.get_summary()
            print(json.dumps(summary, indent=2))
        except FileNotFoundError:
            print(f"ERROR: State file not found: {state_file}")
            sys.exit(1)

    else:
        print(f"ERROR: Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
