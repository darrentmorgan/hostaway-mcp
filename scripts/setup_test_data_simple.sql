-- Setup local test data for pagination testing
-- Simple version without variables

BEGIN;

-- Disable RLS temporarily
ALTER TABLE IF EXISTS organizations DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS api_keys DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS hostaway_credentials DISABLE ROW LEVEL SECURITY;

-- Create a test user in auth.users first (required for foreign key)
INSERT INTO auth.users (
    id,
    email,
    encrypted_password,
    email_confirmed_at,
    created_at,
    updated_at,
    raw_app_meta_data,
    raw_user_meta_data,
    is_super_admin,
    role,
    aud,
    instance_id
)
VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    'test@example.com',
    '$2a$10$VQz9FJ.KZVNFx6dLYkRECug8K8pUaW.KfFDC3U/aM.Bkq2v5f0BgO',  -- bcrypt hash of "password"
    now(),
    now(),
    now(),
    '{"provider":"email","providers":["email"]}'::jsonb,
    '{}'::jsonb,
    false,
    'authenticated',
    'authenticated',
    '00000000-0000-0000-0000-000000000000'
)
ON CONFLICT (id) DO NOTHING;

-- 1. Create test organization
INSERT INTO organizations (name, owner_user_id, created_at, updated_at)
VALUES (
    'Test Organization',
    '00000000-0000-0000-0000-000000000001'::uuid,
    now(),
    now()
)
ON CONFLICT DO NOTHING;

-- 2. Create test API key
-- SHA-256 hash of "test-key-12345" = f7c3bc1d808e04732adf679965ccc34ca7ae3441d3d4d3a2e4e0e73ba7e5e2a3
INSERT INTO api_keys (
    organization_id,
    key_hash,
    created_by_user_id,
    is_active,
    created_at
)
SELECT
    o.id,
    'f7c3bc1d808e04732adf679965ccc34ca7ae3441d3d4d3a2e4e0e73ba7e5e2a3',
    '00000000-0000-0000-0000-000000000001'::uuid,
    true,
    now()
FROM organizations o
WHERE o.name = 'Test Organization'
ON CONFLICT DO NOTHING;

-- 3. Create Hostaway credentials
-- First encrypt the test secret
DO $$
DECLARE
    v_org_id INT;
    v_encrypted_secret TEXT;
BEGIN
    -- Get organization ID
    SELECT id INTO v_org_id
    FROM organizations
    WHERE name = 'Test Organization';

    -- Encrypt test secret key
    SELECT encrypt_hostaway_credential('test_secret_key_12345') INTO v_encrypted_secret;

    -- Insert credentials
    INSERT INTO hostaway_credentials (
        organization_id,
        account_id,
        encrypted_secret_key,
        credentials_valid,
        created_at,
        updated_at
    )
    VALUES (
        v_org_id,
        'TEST_ACC_001',
        v_encrypted_secret,
        true,
        now(),
        now()
    )
    ON CONFLICT DO NOTHING;
END $$;

-- Re-enable RLS
ALTER TABLE IF EXISTS organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS hostaway_credentials ENABLE ROW LEVEL SECURITY;

COMMIT;

-- Display summary
SELECT
    'Test data created!' AS status,
    o.id AS organization_id,
    ak.id AS api_key_id,
    'test-key-12345' AS test_api_key,
    hc.account_id AS hostaway_account_id
FROM organizations o
JOIN api_keys ak ON ak.organization_id = o.id
JOIN hostaway_credentials hc ON hc.organization_id = o.id
WHERE o.name = 'Test Organization';
