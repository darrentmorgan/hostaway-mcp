-- Setup local test data for pagination testing
-- Run with: psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -f setup_test_data.sql

-- Disable RLS temporarily for setup
ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys DISABLE ROW LEVEL SECURITY;
ALTER TABLE hostaway_credentials DISABLE ROW LEVEL SECURITY;

-- 1. Create test organization
INSERT INTO organizations (name, owner_user_id)
VALUES ('Test Organization', gen_random_uuid())
RETURNING id AS organization_id
\gset

-- 2. Create test API key (test-key-12345)
-- SHA-256 hash of "test-key-12345"
INSERT INTO api_keys (organization_id, key_hash, created_by_user_id, is_active)
VALUES (
    :organization_id,
    'f7c3bc1d808e04732adf679965ccc34ca7ae3441d3d4d3a2e4e0e73ba7e5e2a3',  -- SHA-256 of "test-key-12345"
    gen_random_uuid(),
    true
)
RETURNING id AS api_key_id
\gset

-- 3. Encrypt and store Hostaway credentials
DO $$
DECLARE
    org_id INT := :organization_id;
    encrypted_secret TEXT;
BEGIN
    -- Encrypt the test secret key
    SELECT encrypt_hostaway_credential('test_secret_key_12345') INTO encrypted_secret;

    -- Store credentials
    INSERT INTO hostaway_credentials (organization_id, account_id, encrypted_secret_key, credentials_valid)
    VALUES (org_id, 'TEST_ACC_001', encrypted_secret, true);
END $$;

-- Re-enable RLS
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE hostaway_credentials ENABLE ROW LEVEL SECURITY;

-- Display test data info
SELECT
    'Test data created successfully!' AS message,
    :organization_id AS organization_id,
    :api_key_id AS api_key_id,
    'test-key-12345' AS test_api_key,
    'TEST_ACC_001' AS hostaway_account_id;

\echo ''
\echo 'Test data setup complete!'
\echo ''
\echo 'You can now test pagination with:'
\echo '  export API_KEY="test-key-12345"'
\echo '  curl -H "X-API-Key: $API_KEY" "http://localhost:8001/api/listings?limit=10"'
