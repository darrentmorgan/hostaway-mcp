-- ====================================================================
-- RLS Policy Tests
-- Purpose: Verify Row-Level Security policies enforce multi-tenant isolation
-- ====================================================================

BEGIN;

-- Load pgTAP extension
CREATE EXTENSION IF NOT EXISTS pgtap;

-- ====================================================================
-- Test Setup: Create Test Users and Organizations
-- ====================================================================

-- Create test users in auth.users
-- Note: In real Supabase, these would be created via auth.signup()
-- For testing, we'll use service role to insert directly
SET LOCAL ROLE postgres;

-- Test User 1 (Org A Owner)
INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, created_at, updated_at)
VALUES
  ('11111111-1111-1111-1111-111111111111'::uuid, 'user1@example.com', 'hashed', NOW(), NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Test User 2 (Org B Owner)
INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, created_at, updated_at)
VALUES
  ('22222222-2222-2222-2222-222222222222'::uuid, 'user2@example.com', 'hashed', NOW(), NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Test User 3 (Org A Member)
INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, created_at, updated_at)
VALUES
  ('33333333-3333-3333-3333-333333333333'::uuid, 'user3@example.com', 'hashed', NOW(), NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Create test organizations
INSERT INTO organizations (id, name, created_at, updated_at)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid, 'Organization A', NOW(), NOW()),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid, 'Organization B', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Create organization memberships
INSERT INTO organization_members (organization_id, user_id, role, created_at)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid, '11111111-1111-1111-1111-111111111111'::uuid, 'owner', NOW()),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid, '22222222-2222-2222-2222-222222222222'::uuid, 'owner', NOW()),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid, '33333333-3333-3333-3333-333333333333'::uuid, 'member', NOW())
ON CONFLICT (organization_id, user_id) DO NOTHING;

-- Create test credentials
INSERT INTO hostaway_credentials (organization_id, account_id, encrypted_secret_key, credentials_valid, created_at, updated_at)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid, 'ACC_A_001', 'encrypted_secret_a', true, NOW(), NOW()),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid, 'ACC_B_001', 'encrypted_secret_b', true, NOW(), NOW())
ON CONFLICT (organization_id) DO NOTHING;

-- Create test API keys
INSERT INTO api_keys (organization_id, key_hash, is_active, created_at)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid, 'hash_a_001', true, NOW()),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid, 'hash_b_001', true, NOW())
ON CONFLICT DO NOTHING;

-- Create test subscriptions
INSERT INTO subscriptions (organization_id, stripe_subscription_id, status, current_quantity, created_at, updated_at)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid, 'sub_a_001', 'active', 5, NOW(), NOW()),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid, 'sub_b_001', 'active', 3, NOW(), NOW())
ON CONFLICT (organization_id) DO NOTHING;

-- Create test usage metrics
INSERT INTO usage_metrics (organization_id, month_year, total_api_requests, unique_tools_used, created_at, updated_at)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid, '2025-10', 100, ARRAY['properties', 'listings'], NOW(), NOW()),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid, '2025-10', 50, ARRAY['reservations'], NOW(), NOW())
ON CONFLICT (organization_id, month_year) DO NOTHING;

-- Create test audit logs
INSERT INTO audit_logs (organization_id, action, details, created_at)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid, 'credential_updated', '{"account_id": "ACC_A_001"}', NOW()),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid, 'api_key_created', '{"key_id": "key_b_001"}', NOW());

-- ====================================================================
-- Test Plan
-- ====================================================================
SELECT plan(28);

-- ====================================================================
-- 1. organizations Table RLS Tests
-- ====================================================================

-- Test: User 1 can see their own organization (Org A)
SET LOCAL ROLE authenticated;
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT results_eq(
  'SELECT id::text FROM organizations',
  ARRAY['aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'],
  'User 1 can only see Organization A'
);

-- Test: User 2 can see their own organization (Org B)
SET LOCAL "request.jwt.claims" TO '{"sub": "22222222-2222-2222-2222-222222222222"}';

SELECT results_eq(
  'SELECT id::text FROM organizations',
  ARRAY['bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'],
  'User 2 can only see Organization B'
);

-- Test: User 1 cannot see Organization B
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT is(
  (SELECT COUNT(*) FROM organizations WHERE id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid),
  0::bigint,
  'User 1 cannot see Organization B'
);

-- ====================================================================
-- 2. organization_members Table RLS Tests
-- ====================================================================

-- Test: User 1 can see their own membership
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT results_eq(
  'SELECT user_id::text FROM organization_members',
  ARRAY['11111111-1111-1111-1111-111111111111'],
  'User 1 can see their own membership'
);

-- Test: User 2 can see their own membership
SET LOCAL "request.jwt.claims" TO '{"sub": "22222222-2222-2222-2222-222222222222"}';

SELECT results_eq(
  'SELECT user_id::text FROM organization_members',
  ARRAY['22222222-2222-2222-2222-222222222222'],
  'User 2 can see their own membership'
);

-- Test: User 1 (owner) can see all Org A members
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT results_eq(
  'SELECT user_id::text FROM organization_members WHERE organization_id = ''aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa''::uuid ORDER BY user_id',
  ARRAY['11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333'],
  'Owner can see all org members'
);

-- Test: User 3 (member) cannot see other members
SET LOCAL "request.jwt.claims" TO '{"sub": "33333333-3333-3333-3333-333333333333"}';

SELECT results_eq(
  'SELECT user_id::text FROM organization_members',
  ARRAY['33333333-3333-3333-3333-333333333333'],
  'Member can only see their own membership'
);

-- Test: User 1 cannot see User 2's membership
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT is(
  (SELECT COUNT(*) FROM organization_members WHERE user_id = '22222222-2222-2222-2222-222222222222'::uuid),
  0::bigint,
  'User 1 cannot see User 2 membership'
);

-- ====================================================================
-- 3. hostaway_credentials Table RLS Tests
-- ====================================================================

-- Test: User 1 can see Org A credentials
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT results_eq(
  'SELECT organization_id::text FROM hostaway_credentials',
  ARRAY['aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'],
  'User 1 can see Org A credentials'
);

-- Test: User 2 can see Org B credentials
SET LOCAL "request.jwt.claims" TO '{"sub": "22222222-2222-2222-2222-222222222222"}';

SELECT results_eq(
  'SELECT organization_id::text FROM hostaway_credentials',
  ARRAY['bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'],
  'User 2 can see Org B credentials'
);

-- Test: User 1 cannot see Org B credentials
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT is(
  (SELECT COUNT(*) FROM hostaway_credentials WHERE organization_id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid),
  0::bigint,
  'User 1 cannot see Org B credentials'
);

-- Test: User 3 (member) can see Org A credentials
SET LOCAL "request.jwt.claims" TO '{"sub": "33333333-3333-3333-3333-333333333333"}';

SELECT results_eq(
  'SELECT organization_id::text FROM hostaway_credentials',
  ARRAY['aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'],
  'Member can see org credentials'
);

-- ====================================================================
-- 4. api_keys Table RLS Tests
-- ====================================================================

-- Test: User 1 can see Org A API keys
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT is(
  (SELECT COUNT(*) FROM api_keys WHERE organization_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid),
  1::bigint,
  'User 1 can see Org A API keys'
);

-- Test: User 2 can see Org B API keys
SET LOCAL "request.jwt.claims" TO '{"sub": "22222222-2222-2222-2222-222222222222"}';

SELECT is(
  (SELECT COUNT(*) FROM api_keys WHERE organization_id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid),
  1::bigint,
  'User 2 can see Org B API keys'
);

-- Test: User 1 cannot see Org B API keys
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT is(
  (SELECT COUNT(*) FROM api_keys WHERE organization_id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid),
  0::bigint,
  'User 1 cannot see Org B API keys'
);

-- Test: User 3 (member) can see Org A API keys
SET LOCAL "request.jwt.claims" TO '{"sub": "33333333-3333-3333-3333-333333333333"}';

SELECT is(
  (SELECT COUNT(*) FROM api_keys WHERE organization_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid),
  1::bigint,
  'Member can see org API keys'
);

-- ====================================================================
-- 5. subscriptions Table RLS Tests
-- ====================================================================

-- Test: User 1 can see Org A subscription
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT results_eq(
  'SELECT organization_id::text FROM subscriptions',
  ARRAY['aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'],
  'User 1 can see Org A subscription'
);

-- Test: User 2 can see Org B subscription
SET LOCAL "request.jwt.claims" TO '{"sub": "22222222-2222-2222-2222-222222222222"}';

SELECT results_eq(
  'SELECT organization_id::text FROM subscriptions',
  ARRAY['bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'],
  'User 2 can see Org B subscription'
);

-- Test: User 1 cannot see Org B subscription
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT is(
  (SELECT COUNT(*) FROM subscriptions WHERE organization_id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid),
  0::bigint,
  'User 1 cannot see Org B subscription'
);

-- ====================================================================
-- 6. usage_metrics Table RLS Tests
-- ====================================================================

-- Test: User 1 can see Org A usage metrics
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT results_eq(
  'SELECT organization_id::text FROM usage_metrics',
  ARRAY['aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'],
  'User 1 can see Org A usage metrics'
);

-- Test: User 2 can see Org B usage metrics
SET LOCAL "request.jwt.claims" TO '{"sub": "22222222-2222-2222-2222-222222222222"}';

SELECT results_eq(
  'SELECT organization_id::text FROM usage_metrics',
  ARRAY['bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'],
  'User 2 can see Org B usage metrics'
);

-- Test: User 1 cannot see Org B usage metrics
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT is(
  (SELECT COUNT(*) FROM usage_metrics WHERE organization_id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid),
  0::bigint,
  'User 1 cannot see Org B usage metrics'
);

-- ====================================================================
-- 7. audit_logs Table RLS Tests
-- ====================================================================

-- Test: User 1 can see Org A audit logs
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT is(
  (SELECT COUNT(*) FROM audit_logs WHERE organization_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid),
  1::bigint,
  'User 1 can see Org A audit logs'
);

-- Test: User 2 can see Org B audit logs
SET LOCAL "request.jwt.claims" TO '{"sub": "22222222-2222-2222-2222-222222222222"}';

SELECT is(
  (SELECT COUNT(*) FROM audit_logs WHERE organization_id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid),
  1::bigint,
  'User 2 can see Org B audit logs'
);

-- Test: User 1 cannot see Org B audit logs
SET LOCAL "request.jwt.claims" TO '{"sub": "11111111-1111-1111-1111-111111111111"}';

SELECT is(
  (SELECT COUNT(*) FROM audit_logs WHERE organization_id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid),
  0::bigint,
  'User 1 cannot see Org B audit logs'
);

-- Test: User 3 (member) can see Org A audit logs
SET LOCAL "request.jwt.claims" TO '{"sub": "33333333-3333-3333-3333-333333333333"}';

SELECT is(
  (SELECT COUNT(*) FROM audit_logs WHERE organization_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid),
  1::bigint,
  'Member can see org audit logs'
);

-- ====================================================================
-- Test Completion
-- ====================================================================
SELECT * FROM finish();

ROLLBACK;
