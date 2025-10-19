"""Unit tests for cursor_codec module.

Tests cursor encoding/decoding, signature verification, TTL validation,
and error handling for malformed/tampered/expired cursors.
"""

import time

import pytest

from src.utils.cursor_codec import (
    CursorCodecError,
    CursorExpiredError,
    CursorTamperedError,
    decode_cursor,
    encode_cursor,
)


class TestEncodeCursor:
    """Test cursor encoding functionality."""

    def test_encode_cursor_basic(self) -> None:
        """Test basic cursor encoding with minimal parameters."""
        cursor = encode_cursor(offset=0, secret="test-secret")

        # Cursor should be non-empty Base64 string
        assert cursor
        assert isinstance(cursor, str)
        # Base64 URL-safe characters
        assert all(
            c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=" for c in cursor
        )

    def test_encode_cursor_with_all_parameters(self) -> None:
        """Test cursor encoding with all optional parameters."""
        timestamp = time.time()  # Use current time to avoid expiration
        cursor = encode_cursor(
            offset=100,
            secret="test-secret",
            timestamp=timestamp,
            order_by="created_desc",
            filters={"status": "confirmed"},
        )

        assert cursor
        # Decode to verify all fields present
        decoded = decode_cursor(cursor, secret="test-secret")
        assert decoded["offset"] == 100
        assert decoded["ts"] == timestamp
        assert decoded["order_by"] == "created_desc"
        assert decoded["filters"] == {"status": "confirmed"}

    def test_encode_cursor_deterministic(self) -> None:
        """Test that encoding with same parameters produces same cursor."""
        timestamp = 1697452800.0
        cursor1 = encode_cursor(offset=50, secret="test-secret", timestamp=timestamp)
        cursor2 = encode_cursor(offset=50, secret="test-secret", timestamp=timestamp)

        assert cursor1 == cursor2

    def test_encode_cursor_different_secrets_produce_different_cursors(self) -> None:
        """Test that different secrets produce different cursors."""
        timestamp = 1697452800.0
        cursor1 = encode_cursor(offset=50, secret="secret-1", timestamp=timestamp)
        cursor2 = encode_cursor(offset=50, secret="secret-2", timestamp=timestamp)

        assert cursor1 != cursor2

    def test_encode_cursor_negative_offset_raises_error(self) -> None:
        """Test that negative offset raises ValueError."""
        with pytest.raises(ValueError, match="offset must be >= 0"):
            encode_cursor(offset=-1, secret="test-secret")

    def test_encode_cursor_size_approximately_100_bytes(self) -> None:
        """Test that cursor size is approximately 100 bytes as per spec."""
        cursor = encode_cursor(
            offset=100,
            secret="test-secret",
            timestamp=1697452800.0,
        )

        # Cursor should be around 100 bytes (allow some variance)
        cursor_size = len(cursor.encode("utf-8"))
        assert 50 <= cursor_size <= 200


class TestDecodeCursor:
    """Test cursor decoding functionality."""

    def test_decode_cursor_basic(self) -> None:
        """Test basic cursor decoding."""
        timestamp = time.time()
        cursor = encode_cursor(offset=50, secret="test-secret", timestamp=timestamp)

        decoded = decode_cursor(cursor, secret="test-secret")

        assert decoded["offset"] == 50
        assert decoded["ts"] == timestamp

    def test_decode_cursor_with_all_fields(self) -> None:
        """Test decoding cursor with all optional fields."""
        timestamp = time.time()
        cursor = encode_cursor(
            offset=100,
            secret="test-secret",
            timestamp=timestamp,
            order_by="created_desc",
            filters={"status": "confirmed", "minPrice": 100},
        )

        decoded = decode_cursor(cursor, secret="test-secret")

        assert decoded["offset"] == 100
        assert decoded["ts"] == timestamp
        assert decoded["order_by"] == "created_desc"
        assert decoded["filters"] == {"status": "confirmed", "minPrice": 100}

    def test_decode_cursor_wrong_secret_raises_tampered_error(self) -> None:
        """Test that wrong secret raises CursorTamperedError."""
        timestamp = time.time()
        cursor = encode_cursor(offset=50, secret="correct-secret", timestamp=timestamp)

        with pytest.raises(CursorTamperedError, match="signature verification failed"):
            decode_cursor(cursor, secret="wrong-secret")

    def test_decode_cursor_expired_raises_expired_error(self) -> None:
        """Test that expired cursor raises CursorExpiredError."""
        old_timestamp = time.time() - 700  # 11+ minutes ago (exceeds 10min TTL)
        cursor = encode_cursor(offset=50, secret="test-secret", timestamp=old_timestamp)

        with pytest.raises(CursorExpiredError, match="Cursor expired"):
            decode_cursor(cursor, secret="test-secret", ttl_seconds=600)

    def test_decode_cursor_custom_ttl(self) -> None:
        """Test decoding with custom TTL."""
        old_timestamp = time.time() - 100  # 100 seconds ago
        cursor = encode_cursor(offset=50, secret="test-secret", timestamp=old_timestamp)

        # Should fail with 60-second TTL
        with pytest.raises(CursorExpiredError):
            decode_cursor(cursor, secret="test-secret", ttl_seconds=60)

        # Should succeed with 200-second TTL
        decoded = decode_cursor(cursor, secret="test-secret", ttl_seconds=200)
        assert decoded["offset"] == 50

    def test_decode_cursor_invalid_base64_raises_error(self) -> None:
        """Test that invalid Base64 raises CursorCodecError."""
        with pytest.raises(CursorCodecError, match="Invalid cursor format"):
            decode_cursor("not-valid-base64!!!", secret="test-secret")

    def test_decode_cursor_missing_payload_raises_error(self) -> None:
        """Test that cursor missing payload raises CursorCodecError."""
        import base64
        import json

        # Create cursor without payload field
        malformed_data = {"sig": "abc123"}
        malformed_json = json.dumps(malformed_data)
        malformed_cursor = base64.urlsafe_b64encode(malformed_json.encode("utf-8")).decode("utf-8")

        with pytest.raises(CursorCodecError, match="missing required field"):
            decode_cursor(malformed_cursor, secret="test-secret")

    def test_decode_cursor_missing_timestamp_raises_error(self) -> None:
        """Test that cursor missing timestamp raises CursorCodecError."""
        import base64
        import hashlib
        import hmac
        import json

        # Create cursor without timestamp but with valid signature
        payload = {"offset": 50}  # Missing "ts"
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        signature = hmac.new(
            b"test-secret",
            payload_json.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        malformed_data = {
            "payload": payload,
            "sig": signature,
        }
        malformed_json = json.dumps(malformed_data)
        malformed_cursor = base64.urlsafe_b64encode(malformed_json.encode("utf-8")).decode("utf-8")

        with pytest.raises(CursorCodecError, match="missing timestamp"):
            decode_cursor(malformed_cursor, secret="test-secret")

    def test_decode_cursor_invalid_offset_raises_error(self) -> None:
        """Test that invalid offset raises CursorCodecError."""
        import base64
        import hashlib
        import hmac
        import json

        # Create cursor with invalid offset but valid signature
        timestamp = time.time()
        payload = {"offset": -10, "ts": timestamp}
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        signature = hmac.new(
            b"test-secret",
            payload_json.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        malformed_data = {
            "payload": payload,
            "sig": signature,
        }
        malformed_json = json.dumps(malformed_data)
        malformed_cursor = base64.urlsafe_b64encode(malformed_json.encode("utf-8")).decode("utf-8")

        with pytest.raises(CursorCodecError, match="Invalid offset"):
            decode_cursor(malformed_cursor, secret="test-secret")


class TestCursorCodecRoundTrip:
    """Test encode/decode round-trip scenarios."""

    def test_round_trip_preserves_data(self) -> None:
        """Test that encode -> decode preserves all data."""
        timestamp = time.time()
        original_data = {
            "offset": 123,
            "order_by": "price_asc",
            "filters": {"minGuests": 2, "city": "NYC"},
        }

        cursor = encode_cursor(
            offset=original_data["offset"],
            secret="test-secret",
            timestamp=timestamp,
            order_by=original_data["order_by"],
            filters=original_data["filters"],
        )

        decoded = decode_cursor(cursor, secret="test-secret")

        assert decoded["offset"] == original_data["offset"]
        assert decoded["order_by"] == original_data["order_by"]
        assert decoded["filters"] == original_data["filters"]
        assert decoded["ts"] == timestamp

    def test_round_trip_multiple_cursors(self) -> None:
        """Test encoding/decoding multiple cursors in sequence."""
        timestamp = time.time()
        cursors = []

        # Encode multiple cursors
        for i in range(5):
            cursor = encode_cursor(
                offset=i * 50,
                secret="test-secret",
                timestamp=timestamp,
            )
            cursors.append(cursor)

        # Decode and verify
        for i, cursor in enumerate(cursors):
            decoded = decode_cursor(cursor, secret="test-secret")
            assert decoded["offset"] == i * 50

    def test_round_trip_with_special_characters_in_filters(self) -> None:
        """Test that special characters in filters are preserved."""
        timestamp = time.time()
        cursor = encode_cursor(
            offset=50,
            secret="test-secret",
            timestamp=timestamp,
            filters={"name": "O'Brien's Place", "description": "A/C & WiFi"},
        )

        decoded = decode_cursor(cursor, secret="test-secret")
        assert decoded["filters"]["name"] == "O'Brien's Place"
        assert decoded["filters"]["description"] == "A/C & WiFi"


class TestCursorCodecPerformance:
    """Test cursor codec performance requirements."""

    def test_encode_performance_under_1ms(self) -> None:
        """Test that encoding completes in under 1ms (spec requirement)."""
        import timeit

        def encode_test() -> None:
            encode_cursor(offset=100, secret="test-secret", timestamp=1697452800.0)

        # Run 1000 iterations and measure average time
        execution_time = timeit.timeit(encode_test, number=1000)
        avg_time_ms = (execution_time / 1000) * 1000

        # Should be well under 1ms per operation
        assert avg_time_ms < 1.0

    def test_decode_performance_under_1ms(self) -> None:
        """Test that decoding completes in under 1ms (spec requirement)."""
        import timeit

        cursor = encode_cursor(offset=100, secret="test-secret", timestamp=time.time())

        def decode_test() -> None:
            decode_cursor(cursor, secret="test-secret")

        # Run 1000 iterations and measure average time
        execution_time = timeit.timeit(decode_test, number=1000)
        avg_time_ms = (execution_time / 1000) * 1000

        # Should be well under 1ms per operation
        assert avg_time_ms < 1.0
