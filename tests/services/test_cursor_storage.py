"""Unit tests for cursor_storage module.

Tests in-memory cursor storage with TTL, cleanup, and thread safety.
"""

import asyncio
import time

from src.services.cursor_storage import CursorStorage, get_cursor_storage


class TestCursorStorage:
    """Test cursor storage functionality."""

    async def test_store_and_retrieve_cursor(self) -> None:
        """Test storing and retrieving a cursor."""
        storage = CursorStorage()

        cursor_data = {
            "offset": 50,
            "timestamp": time.time(),
            "order_by": "created_desc",
        }

        await storage.store("cursor-1", cursor_data)
        retrieved = await storage.retrieve("cursor-1")

        assert retrieved == cursor_data

    async def test_retrieve_nonexistent_cursor(self) -> None:
        """Test retrieving nonexistent cursor returns None."""
        storage = CursorStorage()

        retrieved = await storage.retrieve("nonexistent")

        assert retrieved is None

    async def test_store_overwrites_existing_cursor(self) -> None:
        """Test that storing with same cursor_id overwrites existing data."""
        storage = CursorStorage()

        await storage.store("cursor-1", {"offset": 50})
        await storage.store("cursor-1", {"offset": 100})

        retrieved = await storage.retrieve("cursor-1")

        assert retrieved == {"offset": 100}

    async def test_delete_cursor(self) -> None:
        """Test deleting a cursor."""
        storage = CursorStorage()

        await storage.store("cursor-1", {"offset": 50})
        await storage.delete("cursor-1")

        retrieved = await storage.retrieve("cursor-1")

        assert retrieved is None

    async def test_delete_nonexistent_cursor(self) -> None:
        """Test deleting nonexistent cursor (should not raise error)."""
        storage = CursorStorage()

        await storage.delete("nonexistent")  # Should not raise

    async def test_clear_all_cursors(self) -> None:
        """Test clearing all cursors."""
        storage = CursorStorage()

        await storage.store("cursor-1", {"offset": 50})
        await storage.store("cursor-2", {"offset": 100})
        await storage.clear_all()

        assert await storage.retrieve("cursor-1") is None
        assert await storage.retrieve("cursor-2") is None


class TestCursorStorageTTL:
    """Test cursor TTL and expiration."""

    async def test_cursor_expires_after_ttl(self) -> None:
        """Test that cursor expires after TTL."""
        storage = CursorStorage(default_ttl=1)  # 1 second TTL

        await storage.store("cursor-1", {"offset": 50})

        # Immediately retrievable
        retrieved = await storage.retrieve("cursor-1")
        assert retrieved is not None

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Should be expired now
        retrieved = await storage.retrieve("cursor-1")
        assert retrieved is None

    async def test_cursor_with_custom_ttl(self) -> None:
        """Test storing cursor with custom TTL."""
        storage = CursorStorage(default_ttl=10)

        # Store with 1-second TTL (overrides default)
        await storage.store("cursor-1", {"offset": 50}, ttl=1)

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Should be expired
        retrieved = await storage.retrieve("cursor-1")
        assert retrieved is None

    async def test_cursor_not_expired_within_ttl(self) -> None:
        """Test that cursor is available within TTL."""
        storage = CursorStorage(default_ttl=5)

        await storage.store("cursor-1", {"offset": 50})

        # Wait half the TTL
        await asyncio.sleep(2.5)

        # Should still be available
        retrieved = await storage.retrieve("cursor-1")
        assert retrieved == {"offset": 50}


class TestCursorStorageCleanup:
    """Test automatic cleanup task."""

    async def test_cleanup_task_starts_and_stops(self) -> None:
        """Test that cleanup task can be started and stopped."""
        storage = CursorStorage()

        await storage.start()
        assert storage._running is True
        assert storage._cleanup_task is not None

        await storage.stop()
        assert storage._running is False

    async def test_cleanup_task_removes_expired_cursors(self) -> None:
        """Test that cleanup task removes expired cursors."""
        storage = CursorStorage(default_ttl=1, cleanup_interval=0.5)

        await storage.start()

        # Store cursors
        await storage.store("cursor-1", {"offset": 50})
        await storage.store("cursor-2", {"offset": 100})

        # Wait for expiration + cleanup
        await asyncio.sleep(2)

        stats = storage.get_stats()
        assert stats["active_cursors"] == 0

        await storage.stop()

    async def test_cleanup_task_preserves_active_cursors(self) -> None:
        """Test that cleanup preserves non-expired cursors."""
        storage = CursorStorage(default_ttl=10, cleanup_interval=0.5)

        await storage.start()

        # Store cursors
        await storage.store("cursor-1", {"offset": 50})
        await storage.store("cursor-2", {"offset": 100})

        # Wait for cleanup cycle (but not long enough for expiration)
        await asyncio.sleep(1)

        stats = storage.get_stats()
        assert stats["active_cursors"] == 2

        await storage.stop()

    async def test_cleanup_task_can_be_stopped_and_restarted(self) -> None:
        """Test that cleanup task can be stopped and restarted."""
        storage = CursorStorage()

        # Start
        await storage.start()
        assert storage._running is True

        # Stop
        await storage.stop()
        assert storage._running is False

        # Restart
        await storage.start()
        assert storage._running is True

        await storage.stop()


class TestCursorStorageStats:
    """Test storage statistics."""

    async def test_get_stats_empty(self) -> None:
        """Test stats for empty storage."""
        storage = CursorStorage()

        stats = storage.get_stats()

        assert stats["total_cursors"] == 0
        assert stats["expired_cursors"] == 0
        assert stats["active_cursors"] == 0

    async def test_get_stats_with_active_cursors(self) -> None:
        """Test stats with active cursors."""
        storage = CursorStorage(default_ttl=10)

        await storage.store("cursor-1", {"offset": 50})
        await storage.store("cursor-2", {"offset": 100})

        stats = storage.get_stats()

        assert stats["total_cursors"] == 2
        assert stats["expired_cursors"] == 0
        assert stats["active_cursors"] == 2

    async def test_get_stats_with_expired_cursors(self) -> None:
        """Test stats with expired cursors."""
        storage = CursorStorage(default_ttl=1)

        await storage.store("cursor-1", {"offset": 50})
        await storage.store("cursor-2", {"offset": 100})

        # Wait for expiration
        await asyncio.sleep(1.5)

        stats = storage.get_stats()

        assert stats["total_cursors"] == 2
        assert stats["expired_cursors"] == 2
        assert stats["active_cursors"] == 0

    async def test_get_stats_mixed_active_and_expired(self) -> None:
        """Test stats with mix of active and expired cursors."""
        storage = CursorStorage(default_ttl=10)

        # Store with different TTLs
        await storage.store("cursor-1", {"offset": 50}, ttl=1)  # Will expire
        await storage.store("cursor-2", {"offset": 100}, ttl=10)  # Will not expire

        # Wait for first to expire
        await asyncio.sleep(1.5)

        stats = storage.get_stats()

        assert stats["total_cursors"] == 2
        assert stats["expired_cursors"] == 1
        assert stats["active_cursors"] == 1


class TestCursorStorageMultipleCursors:
    """Test storage with multiple cursors."""

    async def test_store_multiple_cursors(self) -> None:
        """Test storing multiple independent cursors."""
        storage = CursorStorage()

        cursors = {f"cursor-{i}": {"offset": i * 50} for i in range(10)}

        # Store all cursors
        for cursor_id, data in cursors.items():
            await storage.store(cursor_id, data)

        # Retrieve and verify all
        for cursor_id, expected_data in cursors.items():
            retrieved = await storage.retrieve(cursor_id)
            assert retrieved == expected_data

    async def test_cursors_expire_independently(self) -> None:
        """Test that cursors with different TTLs expire independently."""
        storage = CursorStorage()

        await storage.store("short-ttl", {"offset": 50}, ttl=1)
        await storage.store("long-ttl", {"offset": 100}, ttl=10)

        # Wait for short TTL to expire
        await asyncio.sleep(1.5)

        assert await storage.retrieve("short-ttl") is None
        assert await storage.retrieve("long-ttl") == {"offset": 100}


class TestGetCursorStorage:
    """Test global singleton accessor."""

    def test_get_cursor_storage_returns_instance(self) -> None:
        """Test that get_cursor_storage returns a CursorStorage instance."""
        storage = get_cursor_storage()

        assert isinstance(storage, CursorStorage)

    def test_get_cursor_storage_returns_same_instance(self) -> None:
        """Test that get_cursor_storage returns singleton instance."""
        storage1 = get_cursor_storage()
        storage2 = get_cursor_storage()

        assert storage1 is storage2


class TestCursorStorageEdgeCases:
    """Test edge cases and error handling."""

    async def test_store_with_zero_ttl(self) -> None:
        """Test storing cursor with zero TTL."""
        storage = CursorStorage()

        await storage.store("cursor-1", {"offset": 50}, ttl=0)

        # Should be immediately expired
        retrieved = await storage.retrieve("cursor-1")
        assert retrieved is None

    async def test_store_with_negative_ttl(self) -> None:
        """Test storing cursor with negative TTL."""
        storage = CursorStorage()

        await storage.store("cursor-1", {"offset": 50}, ttl=-1)

        # Should be immediately expired
        retrieved = await storage.retrieve("cursor-1")
        assert retrieved is None

    async def test_store_large_data(self) -> None:
        """Test storing large cursor data."""
        storage = CursorStorage()

        large_data = {
            "offset": 50,
            "filters": {f"field_{i}": f"value_{i}" for i in range(1000)},
        }

        await storage.store("cursor-1", large_data)
        retrieved = await storage.retrieve("cursor-1")

        assert retrieved == large_data

    async def test_concurrent_operations(self) -> None:
        """Test concurrent store/retrieve operations."""
        storage = CursorStorage()

        async def store_cursor(i: int) -> None:
            await storage.store(f"cursor-{i}", {"offset": i * 50})

        async def retrieve_cursor(i: int) -> dict | None:
            return await storage.retrieve(f"cursor-{i}")

        # Store concurrently
        await asyncio.gather(*[store_cursor(i) for i in range(100)])

        # Retrieve concurrently
        results = await asyncio.gather(*[retrieve_cursor(i) for i in range(100)])

        # All should be retrieved successfully
        for i, result in enumerate(results):
            assert result == {"offset": i * 50}
