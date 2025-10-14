"""Hostaway credential validation and expiration detection"""

from datetime import datetime
from typing import NamedTuple

import httpx


class DecryptedCredentials(NamedTuple):
    """Decrypted Hostaway credentials for API requests."""

    account_id: str
    secret_key: str


async def check_credential_validity(account_id: str, secret_key: str) -> dict:
    """Test Hostaway credentials by making API call"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.hostaway.com/v1/listings",
                headers={
                    "Authorization": f"Bearer {secret_key}",
                    "Content-type": "application/json",
                },
                params={"limit": 1},
            )

            if response.status_code == 401:
                return {"valid": False, "error": "Invalid or expired credentials"}
            if response.status_code == 200:
                return {"valid": True, "validated_at": datetime.now(tz=None).isoformat()}
            return {"valid": False, "error": f"Unexpected status: {response.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}
