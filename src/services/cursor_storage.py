"""In-memory cursor storage with TTL cleanup.

Provides thread-safe cursor caching with automatic expiration.
Based on research.md R005: In-memory dict with TTL (initial implementation).
"""

import asyncio
import time
from typing import Any


class CursorStorage:
    """In-memory cursor storage with automatic TTL-based cleanup.

    Thread-safe storage for pagination cursors with configurable TTL.
    Runs background task to periodically remove expired cursors.

    Attributes:
        default_ttl: Default TTL for cursors in seconds (default: 600 = 10 minutes)
        cleanup_interval: Interval between cleanup runs in seconds (default: 60)
    """

    def __init__(
        self,
        default_ttl: int = 600,
        cleanup_interval: int = 60,
    ) -> None:
        """Initialize cursor storage.

        Args:
            default_ttl: Default cursor TTL in seconds
            cleanup_interval: Cleanup task interval in seconds
        """
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self._storage: dict[str, dict[str, Any]] = {}
        self._cleanup_task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        """Start background cleanup task."""
        if not self._running:
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop background cleanup task."""
        self._running = False
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self) -> None:
        """Background task to remove expired cursors."""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break

    async def _cleanup_expired(self) -> None:
        """Remove expired cursors from storage."""
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self._storage.items()
            if current_time - entry["timestamp"] > entry["ttl"]
        ]

        for key in expired_keys:
            del self._storage[key]

    async def store(
        self,
        cursor_id: str,
        data: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Store cursor data with TTL.

        Args:
            cursor_id: Unique cursor identifier
            data: Cursor data to store
            ttl: TTL in seconds (uses default_ttl if None)
        """
        if ttl is None:
            ttl = self.default_ttl

        self._storage[cursor_id] = {
            "data": data,
            "timestamp": time.time(),
            "ttl": ttl,
        }

    async def retrieve(self, cursor_id: str) -> dict[str, Any] | None:
        """Retrieve cursor data if not expired.

        Args:
            cursor_id: Cursor identifier to retrieve

        Returns:
            Cursor data if found and not expired, None otherwise
        """
        entry = self._storage.get(cursor_id)
        if entry is None:
            return None

        # Check if expired
        current_time = time.time()
        if current_time - entry["timestamp"] > entry["ttl"]:
            # Remove expired cursor
            del self._storage[cursor_id]
            return None

        return entry["data"]

    async def delete(self, cursor_id: str) -> None:
        """Delete cursor from storage.

        Args:
            cursor_id: Cursor identifier to delete
        """
        self._storage.pop(cursor_id, None)

    async def clear_all(self) -> None:
        """Clear all cursors from storage."""
        self._storage.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dict with keys: total_cursors, expired_cursors
        """
        current_time = time.time()
        total_cursors = len(self._storage)
        expired_cursors = sum(
            1
            for entry in self._storage.values()
            if current_time - entry["timestamp"] > entry["ttl"]
        )

        return {
            "total_cursors": total_cursors,
            "expired_cursors": expired_cursors,
            "active_cursors": total_cursors - expired_cursors,
        }


# Global singleton instance (lazy initialization)
_cursor_storage: CursorStorage | None = None


def get_cursor_storage() -> CursorStorage:
    """Get global cursor storage instance.

    Returns:
        Singleton CursorStorage instance
    """
    global _cursor_storage
    if _cursor_storage is None:
        _cursor_storage = CursorStorage()
    return _cursor_storage
