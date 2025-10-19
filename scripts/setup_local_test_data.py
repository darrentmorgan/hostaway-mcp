#!/usr/bin/env python3
"""Setup local test data for pagination testing.

Creates:
- Test organization
- Test API key (test-key-12345)
- Test Hostaway credentials
"""

import hashlib
import uuid

from supabase import create_client

# Supabase local connection
SUPABASE_URL = "http://127.0.0.1:54321"
SUPABASE_KEY = "sb_service_N7UND0UgjKTVK-Uodkm0Hg_xSvEMPvz"  # Service role key

# Test data
TEST_API_KEY = "test-key-12345"
TEST_ACCOUNT_ID = "TEST_ACC_001"
TEST_SECRET_KEY = "test_secret_key_12345"


def hash_api_key(api_key: str) -> str:
    """Hash API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def main():
    """Create test data in local Supabase."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY, options={"auth": {"persistSession": False}})

    print("Setting up local test data...")

    # 1. Create test organization
    print("\n1. Creating test organization...")
    org_response = (
        client.table("organizations")
        .insert(
            {
                "name": "Test Organization",
                "owner_user_id": str(uuid.uuid4()),
            }
        )
        .execute()
    )
    org_id = org_response.data[0]["id"]
    print(f"   Created organization with ID: {org_id}")

    # 2. Create API key
    print("\n2. Creating test API key...")
    key_hash = hash_api_key(TEST_API_KEY)
    api_key_response = (
        client.table("api_keys")
        .insert(
            {
                "organization_id": org_id,
                "key_hash": key_hash,
                "created_by_user_id": str(uuid.uuid4()),
                "is_active": True,
            }
        )
        .execute()
    )
    api_key_id = api_key_response.data[0]["id"]
    print(f"   Created API key with ID: {api_key_id}")
    print(f"   API Key: {TEST_API_KEY}")
    print(f"   Key Hash: {key_hash}")

    # 3. Encrypt and store Hostaway credentials
    print("\n3. Creating Hostaway credentials...")

    # Encrypt the secret key using Vault
    encrypt_response = client.rpc(
        "encrypt_hostaway_credential",
        {"plain_secret": TEST_SECRET_KEY},
    ).execute()

    encrypted_secret = encrypt_response.data

    # Store credentials
    creds_response = (
        client.table("hostaway_credentials")
        .insert(
            {
                "organization_id": org_id,
                "account_id": TEST_ACCOUNT_ID,
                "encrypted_secret_key": encrypted_secret,
                "credentials_valid": True,
            }
        )
        .execute()
    )
    creds_id = creds_response.data[0]["id"]
    print(f"   Created credentials with ID: {creds_id}")
    print(f"   Account ID: {TEST_ACCOUNT_ID}")

    print("\n✅ Test data setup complete!")
    print("\nYou can now test pagination with:")
    print(f'export API_KEY="{TEST_API_KEY}"')
    print('curl -H "X-API-Key: $API_KEY" "http://localhost:8001/api/listings?limit=10"')


if __name__ == "__main__":
    main()
