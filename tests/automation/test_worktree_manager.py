"""Tests for worktree-manager.sh"""

from pathlib import Path

import pytest


@pytest.fixture
def worktree_manager():
    """Path to worktree-manager.sh script."""
    return Path(__file__).parent.parent.parent / ".automation" / "scripts" / "worktree-manager.sh"


def test_worktree_manager_exists(worktree_manager):
    """Test that worktree-manager.sh script exists."""
    assert worktree_manager.exists(), "worktree-manager.sh not found"
    assert worktree_manager.is_file(), "worktree-manager.sh is not a file"


@pytest.mark.skip(reason="Requires worktree-manager.sh implementation")
def test_worktree_create(worktree_manager):
    """Test creating a worktree."""
    # TODO: Implement after worktree-manager.sh is created


@pytest.mark.skip(reason="Requires worktree-manager.sh implementation")
def test_worktree_delete(worktree_manager):
    """Test deleting a worktree."""
    # TODO: Implement after worktree-manager.sh is created


@pytest.mark.skip(reason="Requires worktree-manager.sh implementation")
def test_worktree_list(worktree_manager):
    """Test listing worktrees."""
    # TODO: Implement after worktree-manager.sh is created
