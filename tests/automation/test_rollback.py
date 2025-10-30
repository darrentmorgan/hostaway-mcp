"""Tests for rollback functionality."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def scripts_dir():
    """Path to automation scripts directory."""
    return Path(__file__).parent.parent.parent / ".automation" / "scripts"


@pytest.fixture
def logs_dir():
    """Path to automation logs directory."""
    return Path(__file__).parent.parent.parent / ".automation" / "logs"


def test_rollback_script_exists(scripts_dir):
    """Test that rollback.sh script exists and is executable."""
    rollback_script = scripts_dir / "rollback.sh"
    assert rollback_script.exists(), "rollback.sh not found"
    assert rollback_script.stat().st_mode & 0o111, "rollback.sh not executable"


def test_rollback_help_option(scripts_dir):
    """Test that rollback.sh responds to --help."""
    rollback_script = scripts_dir / "rollback.sh"

    result = subprocess.run(
        [str(rollback_script), "--help"], check=False, capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "--force" in result.stdout
    assert "--fix-id" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--create-backup" in result.stdout


def test_rollback_requires_checkpoint(scripts_dir, logs_dir, tmp_path, monkeypatch):
    """Test that rollback fails gracefully when no checkpoint exists."""
    # Use temporary logs directory
    temp_logs = tmp_path / "logs"
    temp_logs.mkdir()

    # Patch LOGS_DIR to use temp directory
    monkeypatch.setenv("LOGS_DIR", str(temp_logs))

    rollback_script = scripts_dir / "rollback.sh"

    result = subprocess.run(
        [str(rollback_script), "--force"],
        check=False,
        capture_output=True,
        text=True,
        env={"LOGS_DIR": str(temp_logs)},
    )

    # Should fail with error about missing checkpoint
    assert result.returncode != 0
    assert "checkpoint" in result.stderr.lower() or "checkpoint" in result.stdout.lower()


def test_dry_run_mode(scripts_dir):
    """Test that --dry-run shows what would be done without making changes."""
    rollback_script = scripts_dir / "rollback.sh"

    # Create fake checkpoint file for testing
    logs_dir = Path(__file__).parent.parent.parent / ".automation" / "logs"
    checkpoint_file = logs_dir / "checkpoint-tag.txt"

    # Skip if no checkpoint exists (this test needs a real checkpoint)
    if not checkpoint_file.exists():
        pytest.skip("No checkpoint tag found - cannot test dry-run mode")

    result = subprocess.run(
        [str(rollback_script), "--dry-run"], check=False, capture_output=True, text=True
    )

    # Dry run should succeed and show planned actions
    assert result.returncode == 0
    assert "DRY RUN" in result.stdout
    assert "No changes will be made" in result.stdout
    assert "would be" in result.stdout.lower()


def test_orchestrator_failure_threshold_integration(scripts_dir):
    """Test that orchestrator accepts failure threshold options."""
    orchestrator_script = scripts_dir / "orchestrator.sh"

    result = subprocess.run(
        [str(orchestrator_script), "--help"], check=False, capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "--failure-threshold" in result.stdout
    assert "--auto-rollback" in result.stdout


def test_orchestrator_dry_run_with_rollback_options(scripts_dir):
    """Test that orchestrator dry-run works with rollback options."""
    orchestrator_script = scripts_dir / "orchestrator.sh"

    result = subprocess.run(
        [str(orchestrator_script), "--dry-run", "--failure-threshold", "30", "--auto-rollback"],
        check=False,
        capture_output=True,
        text=True,
    )

    # Dry run should work (may fail due to missing config, but shouldn't error on args)
    assert "--failure-threshold" not in result.stderr or result.returncode == 0


def test_selective_rollback_help(scripts_dir):
    """Test that selective rollback option is documented."""
    rollback_script = scripts_dir / "rollback.sh"

    result = subprocess.run(
        [str(rollback_script), "--help"], check=False, capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "--fix-id" in result.stdout
    assert "Rollback specific fix only" in result.stdout


def test_backup_creation_option(scripts_dir):
    """Test that --create-backup option is available."""
    rollback_script = scripts_dir / "rollback.sh"

    result = subprocess.run(
        [str(rollback_script), "--help"], check=False, capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "--create-backup" in result.stdout
    assert "backup" in result.stdout.lower()


@pytest.mark.skip(reason="Integration test - requires git repo and checkpoint")
def test_rollback_execution_flow():
    """Integration test: Test full rollback execution.

    This test requires:
    - Git repository
    - Checkpoint tag created
    - Worktrees created
    - State file present

    Skipped for unit tests.
    """


@pytest.mark.skip(reason="Integration test - requires git repo")
def test_selective_rollback_execution():
    """Integration test: Test selective rollback of a single fix.

    This test requires:
    - Git repository
    - Specific fix worktree created
    - Branch for fix exists

    Skipped for unit tests.
    """


@pytest.mark.skip(reason="Integration test - requires git repo")
def test_backup_creation():
    """Integration test: Test git bundle backup creation.

    This test requires:
    - Git repository with commits
    - Write access to logs directory

    Skipped for unit tests.
    """


@pytest.mark.skip(reason="Integration test - requires orchestrator state")
def test_automatic_rollback_on_threshold():
    """Integration test: Test automatic rollback when failure threshold exceeded.

    This test requires:
    - Running orchestrator
    - Simulated failures
    - Checkpoint created

    Skipped for unit tests.
    """
