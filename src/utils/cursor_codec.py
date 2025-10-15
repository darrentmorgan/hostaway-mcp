"""Cursor encoding/decoding utility with HMAC-SHA256 signature.

Provides tamper-proof, opaque cursor tokens for pagination with 10-minute TTL.
Based on research.md R002: Base64 + HMAC-SHA256 encoding strategy.
"""

import base64
import hmac
import json
import time
from hashlib import sha256
from typing import Any


class CursorCodecError(Exception):
    """Raised when cursor encoding/decoding fails."""


class CursorExpiredError(CursorCodecError):
    """Raised when cursor has exceeded its 10-minute TTL."""


class CursorTamperedError(CursorCodecError):
    """Raised when cursor signature verification fails."""


def encode_cursor(
    offset: int,
    secret: str,
    timestamp: float | None = None,
    order_by: str | None = None,
    filters: dict[str, Any] | None = None,
) -> str:
    """Encode pagination cursor with HMAC signature.

    Args:
        offset: Current position in result set (>= 0)
        secret: HMAC secret key for signing
        timestamp: Cursor creation time (Unix timestamp). Defaults to current time.
        order_by: Sort column and direction (e.g., "created_desc")
        filters: Query filters at cursor creation time

    Returns:
        Base64-encoded cursor string with embedded signature (~100 bytes)

    Example:
        >>> cursor = encode_cursor(offset=50, secret="my-secret")
        >>> cursor
        'eyJwYXlsb2FkIjp7Im9mZnNldCI6NTAsInRzIjoxNjk3NDUyODAwLjB9LCJzaWciOiJhYmMxMjMuLi4ifQ=='
    """
    if offset < 0:
        raise ValueError("offset must be >= 0")

    if timestamp is None:
        timestamp = time.time()

    # Build payload
    payload: dict[str, Any] = {
        "offset": offset,
        "ts": timestamp,
    }
    if order_by is not None:
        payload["order_by"] = order_by
    if filters is not None:
        payload["filters"] = filters

    # Sign payload
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signature = hmac.new(
        secret.encode("utf-8"),
        payload_json.encode("utf-8"),
        sha256,
    ).hexdigest()

    # Combine payload + signature
    cursor_data = {
        "payload": payload,
        "sig": signature,
    }
    cursor_json = json.dumps(cursor_data, separators=(",", ":"))

    # Base64 encode
    return base64.urlsafe_b64encode(cursor_json.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor: str, secret: str, ttl_seconds: int = 600) -> dict[str, Any]:
    """Decode and validate pagination cursor.

    Args:
        cursor: Base64-encoded cursor string
        secret: HMAC secret key for verification
        ttl_seconds: Cursor TTL in seconds (default 600 = 10 minutes)

    Returns:
        Decoded payload dict with keys: offset, ts, order_by (optional), filters (optional)

    Raises:
        CursorCodecError: If cursor is malformed or invalid Base64
        CursorTamperedError: If signature verification fails
        CursorExpiredError: If cursor has exceeded TTL

    Example:
        >>> payload = decode_cursor(cursor, secret="my-secret")
        >>> payload
        {'offset': 50, 'ts': 1697452800.0, 'order_by': 'created_desc'}
    """
    try:
        # Base64 decode
        cursor_json = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        cursor_data = json.loads(cursor_json)
    except (ValueError, KeyError) as e:
        raise CursorCodecError(f"Invalid cursor format: {e}") from e

    # Extract payload and signature
    try:
        payload = cursor_data["payload"]
        provided_sig = cursor_data["sig"]
    except KeyError as e:
        raise CursorCodecError(f"Cursor missing required field: {e}") from e

    # Verify signature
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        payload_json.encode("utf-8"),
        sha256,
    ).hexdigest()

    if not hmac.compare_digest(provided_sig, expected_sig):
        raise CursorTamperedError("Cursor signature verification failed")

    # Verify TTL
    cursor_timestamp = payload.get("ts")
    if cursor_timestamp is None:
        raise CursorCodecError("Cursor missing timestamp")

    current_time = time.time()
    if current_time - cursor_timestamp > ttl_seconds:
        raise CursorExpiredError(
            f"Cursor expired (age: {current_time - cursor_timestamp:.1f}s, TTL: {ttl_seconds}s)"
        )

    # Validate offset
    if not isinstance(payload.get("offset"), int) or payload["offset"] < 0:
        raise CursorCodecError("Invalid offset in cursor")

    return payload
