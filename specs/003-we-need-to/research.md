# Research: Multi-Tenant Billable MCP Server (v2.0)

**Date**: 2025-10-13
**Branch**: `003-we-need-to`
**Phase**: 0 (Research & Discovery)

---

## Research Tasks

Based on Technical Context unknowns, the following research areas must be explored:

1. **R1**: Supabase Row Level Security (RLS) patterns for multi-tenancy
2. **R2**: Supabase Vault (pgsodium) for credential encryption
3. **R3**: Next.js 14 App Router with Supabase Auth integration
4. **R4**: Stripe subscription API with quantity-based metering
5. **R5**: Supabase Edge Functions for webhook handling
6. **R6**: FastAPI-Supabase integration patterns
7. **R7**: Multi-tenant testing strategies (RLS enforcement verification)

---

## R1: Supabase Row Level Security (RLS) Patterns for Multi-Tenancy

### Decision

Use **Supabase RLS policies** to enforce organization-level data isolation at the database layer. All application tables will have RLS enabled with policies that filter rows based on the authenticated user's organization membership.

### Research Findings

**RLS Policy Pattern**:
```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE hostaway_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access data from organizations they belong to
CREATE POLICY "Users access own org data" ON organizations
  FOR ALL
  USING (
    id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
    )
  );

-- Policy: API keys scoped to user's organization
CREATE POLICY "Users manage own org API keys" ON api_keys
  FOR ALL
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
    )
  );

-- Policy: Hostaway credentials scoped to user's organization
CREATE POLICY "Users access own org credentials" ON hostaway_credentials
  FOR SELECT
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
    )
  );
```

**Key Insights**:
1. **auth.uid()** function returns the current authenticated user's ID from Supabase Auth JWT
2. RLS policies are **evaluated on every query** - no application-level filtering needed
3. Policies use **subquery pattern** to check organization membership via `organization_members` table
4. **Service role key bypasses RLS** - FastAPI backend must use service role key carefully (only for API key validation)

**Security Benefits**:
- Database enforces isolation (cannot be bypassed by application bugs)
- Zero-trust architecture (even if FastAPI is compromised, database blocks cross-org access)
- Automatic filtering (developers don't need to remember to add WHERE clauses)

**Performance Considerations**:
- RLS policies add subquery overhead (~1-5ms per query)
- Index on `organization_members(user_id, organization_id)` critical for performance
- Use `USING` clause for SELECT, `WITH CHECK` for INSERT/UPDATE to prevent bypasses

**Alternatives Considered**:
- **Application-level filtering**: Rejected - requires manual WHERE clauses, easy to forget, error-prone
- **Separate databases per tenant**: Rejected - too expensive, complex migration, not needed at current scale
- **Schema-based multi-tenancy**: Rejected - PostgreSQL has schema limits, Supabase doesn't support well

**Rationale**: RLS provides database-level isolation with minimal performance impact and zero application complexity.

---

## R2: Supabase Vault (pgsodium) for Credential Encryption

### Decision

Use **Supabase Vault** (backed by pgsodium PostgreSQL extension) to encrypt Hostaway credentials at rest. Encryption keys are managed by Supabase and stored in hardware security modules (HSMs).

### Research Findings

**Vault Encryption Pattern**:
```sql
-- Enable pgsodium extension
CREATE EXTENSION IF NOT EXISTS pgsodium;

-- Create secret for encrypting Hostaway credentials
INSERT INTO vault.secrets (name, secret)
VALUES ('hostaway_encryption_key', pgsodium.crypto_secretbox_keygen());

-- Store encrypted credentials
CREATE TABLE hostaway_credentials (
  id BIGSERIAL PRIMARY KEY,
  organization_id BIGINT REFERENCES organizations(id),
  account_id TEXT NOT NULL,
  encrypted_secret_key TEXT NOT NULL, -- encrypted with pgsodium
  credentials_valid BOOLEAN DEFAULT true,
  last_validated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Encrypt on insert
INSERT INTO hostaway_credentials (organization_id, account_id, encrypted_secret_key)
VALUES (
  123,
  'ACC_12345',
  pgsodium.crypto_secretbox(
    'secret_key_value'::bytea,
    (SELECT secret FROM vault.secrets WHERE name = 'hostaway_encryption_key')
  )
);

-- Decrypt on select (service role only)
SELECT
  organization_id,
  account_id,
  pgsodium.crypto_secretbox_open(
    encrypted_secret_key::bytea,
    (SELECT secret FROM vault.secrets WHERE name = 'hostaway_encryption_key')
  )::text AS secret_key
FROM hostaway_credentials
WHERE organization_id = 123;
```

**Key Insights**:
1. **pgsodium.crypto_secretbox**: Uses XSalsa20-Poly1305 authenticated encryption (same as NaCl/libsodium)
2. **vault.secrets table**: Stores encryption keys, **accessible only by service role** (not anon key)
3. **Automatic key rotation**: Supabase manages HSM-backed keys, rotates periodically
4. **Decryption in application**: FastAPI backend must decrypt using service role key (bypasses RLS)

**Security Benefits**:
- Encryption at rest (even database administrators cannot read credentials without vault access)
- Hardware-backed keys (HSM ensures keys never leave secure boundary)
- Compliance-ready (GDPR, SOC 2 compliant encryption)

**Performance Considerations**:
- Encryption/decryption adds ~2-5ms per operation
- Decryption happens in FastAPI backend (not in database) to avoid exposing decrypted values
- Cache decrypted credentials per request (don't decrypt on every tool invocation)

**Alternatives Considered**:
- **Application-level encryption (AES-256 in Python)**: Rejected - requires managing encryption keys in env vars, less secure
- **AWS KMS**: Rejected - adds external dependency, Supabase Vault is integrated and free
- **HashiCorp Vault**: Rejected - separate service, more complexity, not needed at current scale

**Rationale**: Supabase Vault provides HSM-backed encryption with zero operational overhead and native PostgreSQL integration.

---

## R3: Next.js 14 App Router with Supabase Auth Integration

### Decision

Use **Next.js 14 App Router** with **@supabase/ssr** library for server-side Supabase Auth integration. Implement Server Components for data fetching and Server Actions for mutations.

### Research Findings

**Supabase Auth Integration Pattern**:
```typescript
// lib/supabase/server.ts - Server Component client
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export function createClient() {
  const cookieStore = cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
      },
    }
  )
}

// app/(dashboard)/page.tsx - Server Component with auth
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const supabase = createClient()

  // Get authenticated user
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  // Get user's organization (RLS enforced)
  const { data: org } = await supabase
    .from('organizations')
    .select('*, api_keys(*), subscriptions(*)')
    .single()

  return <DashboardView org={org} user={user} />
}

// app/api/api-keys/route.ts - Server Action for API key generation
import { createClient } from '@/lib/supabase/server'
import crypto from 'crypto'

export async function POST() {
  const supabase = createClient()

  // Get user's org (RLS enforced)
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return new Response('Unauthorized', { status: 401 })

  const { data: orgMember } = await supabase
    .from('organization_members')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  // Generate API key
  const apiKey = crypto.randomBytes(32).toString('hex')
  const keyHash = crypto.createHash('sha256').update(apiKey).digest('hex')

  // Store hash in Supabase (RLS enforced)
  await supabase.from('api_keys').insert({
    organization_id: orgMember.organization_id,
    key_hash: keyHash,
    created_by_user_id: user.id
  })

  // Return full key ONCE
  return Response.json({ api_key: apiKey })
}
```

**Key Insights**:
1. **@supabase/ssr**: Handles cookie-based sessions in Next.js App Router (Server Components + Server Actions)
2. **Server Components**: Fetch data on server, no client-side waterfalls, RLS policies enforced automatically
3. **Server Actions**: Mutations run on server, inherently secure (no exposing logic to client)
4. **Automatic session refresh**: @supabase/ssr handles token refresh transparently

**Authentication Flow**:
1. User signs in → Supabase Auth sets JWT in httpOnly cookie
2. Server Component reads cookie → validates JWT → extracts user_id
3. Supabase queries use user_id in RLS policies → auto-filter by organization
4. No manual session management needed (all handled by @supabase/ssr)

**Performance Benefits**:
- Server Components eliminate client-side rendering overhead
- Data fetching happens on server (closer to database)
- Parallel data fetching via React Suspense

**Alternatives Considered**:
- **Pages Router + getServerSideProps**: Rejected - App Router is newer, better performance, simpler auth
- **Client-side rendering + SWR**: Rejected - slower initial load, RLS policies require server-side auth
- **Next-Auth (Auth.js)**: Rejected - Supabase Auth is integrated with database, no need for separate provider

**Rationale**: Next.js 14 App Router + @supabase/ssr provides seamless server-side auth with minimal boilerplate and automatic RLS enforcement.

---

## R4: Stripe Subscription API with Quantity-Based Metering

### Decision

Use **Stripe Subscriptions API** with **quantity-based pricing** to bill organizations per active listing. Implement daily sync job to update subscription quantity based on Hostaway listing count, with automatic proration.

### Research Findings

**Stripe Subscription Pattern**:
```typescript
// Create subscription on organization signup
import Stripe from 'stripe'
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

async function createSubscription(orgId: number, listingCount: number) {
  // Create Stripe customer
  const customer = await stripe.customers.create({
    email: user.email,
    metadata: { organization_id: orgId }
  })

  // Create subscription with quantity = listing count
  const subscription = await stripe.subscriptions.create({
    customer: customer.id,
    items: [{
      price: 'price_listing_monthly', // $5/listing/month
      quantity: listingCount
    }],
    proration_behavior: 'create_prorations', // Auto-prorate on quantity changes
    metadata: { organization_id: orgId }
  })

  // Store subscription ID in Supabase
  await supabase.from('subscriptions').insert({
    organization_id: orgId,
    stripe_subscription_id: subscription.id,
    stripe_customer_id: customer.id,
    current_quantity: listingCount,
    status: subscription.status
  })

  return subscription
}

// Update subscription quantity (daily sync job)
async function updateSubscriptionQuantity(orgId: number, newListingCount: number) {
  // Get subscription from Supabase
  const { data: sub } = await supabase
    .from('subscriptions')
    .select('stripe_subscription_id, current_quantity')
    .eq('organization_id', orgId)
    .single()

  if (sub.current_quantity === newListingCount) return // No change

  // Update Stripe subscription quantity
  const subscription = await stripe.subscriptions.retrieve(sub.stripe_subscription_id)
  await stripe.subscriptions.update(sub.stripe_subscription_id, {
    items: [{
      id: subscription.items.data[0].id,
      quantity: newListingCount
    }],
    proration_behavior: 'create_prorations' // Prorate the difference
  })

  // Update Supabase
  await supabase.from('subscriptions').update({
    current_quantity: newListingCount
  }).eq('organization_id', orgId)
}
```

**Key Insights**:
1. **Quantity-based pricing**: Stripe automatically calculates `quantity * unit_price` per billing cycle
2. **Automatic proration**: When quantity changes mid-cycle, Stripe creates prorated invoice items (credit/charge)
3. **Metadata for mapping**: Store `organization_id` in Stripe customer/subscription metadata for webhook processing
4. **Subscription statuses**: active, past_due, canceled, trialing - must handle all states

**Billing Flow**:
1. **Signup**: Create subscription with initial listing count
2. **Daily sync**: Fetch listing count from Hostaway → update Stripe subscription quantity
3. **Stripe invoices**: Generated monthly, includes prorations from quantity changes
4. **Payment failure**: Webhook triggers → suspend API keys → notify user

**Performance Considerations**:
- Daily sync job runs asynchronously (not blocking user requests)
- Stripe API rate limits: 100 req/s (sufficient for 10K orgs with 1 sync/day/org)
- Cache listing count in Supabase to avoid excessive Hostaway API calls

**Alternatives Considered**:
- **Metered billing (usage-based)**: Rejected - requires reporting usage events, more complex, listing count is simpler
- **Fixed tiers (0-10 listings, 11-50, etc.)**: Rejected - unfair for users at tier boundaries, quantity-based is fairer
- **Annual billing**: Rejected - monthly is safer for MVP, can add annual later

**Rationale**: Quantity-based subscriptions with automatic proration provide transparent, fair billing with minimal operational overhead.

---

## R5: Supabase Edge Functions for Webhook Handling

### Decision

Use **Supabase Edge Functions** (Deno runtime) to handle Stripe webhooks. Edge Functions provide secure webhook processing with built-in signature verification and direct database access.

### Research Findings

**Stripe Webhook Edge Function Pattern**:
```typescript
// supabase/functions/stripe-webhook/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import Stripe from 'https://esm.sh/stripe@14.0.0'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY')!, {
  httpClient: Stripe.createFetchHttpClient(),
})

serve(async (req) => {
  const signature = req.headers.get('stripe-signature')!
  const body = await req.text()

  // Verify webhook signature
  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      Deno.env.get('STRIPE_WEBHOOK_SECRET')!
    )
  } catch (err) {
    return new Response(`Webhook signature verification failed: ${err.message}`, { status: 400 })
  }

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_KEY')! // Service role for RLS bypass
  )

  // Handle events
  switch (event.type) {
    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice
      const orgId = invoice.subscription_metadata?.organization_id

      // Suspend API keys
      await supabase
        .from('api_keys')
        .update({ is_active: false })
        .eq('organization_id', orgId)

      // Update subscription status
      await supabase
        .from('subscriptions')
        .update({ status: 'past_due' })
        .eq('organization_id', orgId)

      break
    }

    case 'invoice.payment_succeeded': {
      const invoice = event.data.object as Stripe.Invoice
      const orgId = invoice.subscription_metadata?.organization_id

      // Restore API keys
      await supabase
        .from('api_keys')
        .update({ is_active: true })
        .eq('organization_id', orgId)

      // Update subscription status
      await supabase
        .from('subscriptions')
        .update({ status: 'active' })
        .eq('organization_id', orgId)

      break
    }

    case 'customer.subscription.deleted': {
      const subscription = event.data.object as Stripe.Subscription
      const orgId = subscription.metadata?.organization_id

      // Mark subscription as canceled
      await supabase
        .from('subscriptions')
        .update({ status: 'canceled' })
        .eq('organization_id', orgId)

      break
    }
  }

  return new Response(JSON.stringify({ received: true }), { status: 200 })
})
```

**Key Insights**:
1. **Deno runtime**: TypeScript-first, secure by default (no file system access unless granted)
2. **Signature verification**: Stripe SDK verifies webhook signature to prevent forgery
3. **Idempotency**: Use Stripe event ID to prevent duplicate processing (store in `processed_webhooks` table)
4. **Service role key**: Edge Function uses service role key to bypass RLS (writes to any org's data)

**Security Benefits**:
- Webhook signature verification prevents unauthorized requests
- Edge Functions run in isolated environment (cannot access other functions' secrets)
- Service role key scoped to database operations only (no file system access)

**Performance Considerations**:
- Edge Functions run globally on Cloudflare network (low latency)
- Auto-scaling: handles webhook bursts (1000s of events/sec)
- Cold start: ~50-100ms (acceptable for async webhooks)

**Alternatives Considered**:
- **FastAPI webhook endpoint**: Rejected - requires VPS to handle webhooks, Edge Functions are serverless
- **AWS Lambda**: Rejected - Supabase Edge Functions are integrated, no separate AWS account needed
- **Vercel Serverless Functions**: Rejected - Supabase Edge Functions have direct database access (no network hop)

**Rationale**: Supabase Edge Functions provide serverless webhook processing with native database integration and zero operational overhead.

---

## R6: FastAPI-Supabase Integration Patterns

### Decision

Integrate **supabase-py** library into FastAPI backend to validate API keys against Supabase database and retrieve organization-scoped Hostaway credentials. Use service role key to bypass RLS for authentication logic.

### Research Findings

**FastAPI-Supabase Integration Pattern**:
```python
# src/services/supabase_client.py
from supabase import create_client, Client
import os

def get_supabase_client() -> Client:
    """Create Supabase client with service role key (bypasses RLS)"""
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")  # Service key for RLS bypass
    )

# src/api/dependencies.py
from fastapi import Header, HTTPException, Depends
from src.services.supabase_client import get_supabase_client
from src.services.credential_service import decrypt_hostaway_credentials
import hashlib

async def get_organization_context(
    x_api_key: str = Header(..., alias="X-API-Key"),
    supabase: Client = Depends(get_supabase_client)
):
    """Validate API key and return organization context"""

    # Hash the provided API key
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()

    # Query Supabase for valid API key (service role bypasses RLS)
    result = supabase.table('api_keys')\
        .select('organization_id, is_active')\
        .eq('key_hash', key_hash)\
        .eq('is_active', True)\
        .execute()

    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid API key")

    org_id = result.data[0]['organization_id']

    # Get organization's Hostaway credentials (encrypted)
    creds = supabase.table('hostaway_credentials')\
        .select('account_id, encrypted_secret_key')\
        .eq('organization_id', org_id)\
        .single()\
        .execute()

    # Decrypt credentials using Supabase Vault
    secret_key = decrypt_hostaway_credentials(creds.data['encrypted_secret_key'])

    # Update last_used_at for API key
    supabase.table('api_keys')\
        .update({'last_used_at': 'now()'})\
        .eq('key_hash', key_hash)\
        .execute()

    return {
        "organization_id": org_id,
        "hostaway_account_id": creds.data['account_id'],
        "hostaway_secret_key": secret_key
    }

# src/api/routes/properties.py
from fastapi import APIRouter, Depends
from src.api.dependencies import get_organization_context
import httpx

router = APIRouter(prefix="/api/properties", tags=["properties"])

@router.get("/")
async def get_properties(
    context = Depends(get_organization_context)
):
    """Get properties for authenticated organization's Hostaway account"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.hostaway.com/v1/listings",
            headers={
                "Authorization": f"Bearer {context['hostaway_secret_key']}",
                "X-Account-Id": context['hostaway_account_id']
            }
        )
        return response.json()
```

**Key Insights**:
1. **Service role key bypasses RLS**: Required for API key validation (can read any org's api_keys table)
2. **Dependency injection**: `Depends(get_organization_context)` provides org context to all endpoints
3. **Credential caching**: Cache decrypted credentials per request to avoid re-decryption
4. **Audit logging**: Log all MCP invocations to Supabase audit_logs table with org_id

**Security Considerations**:
- Service role key stored in env var (never committed to code)
- Decrypted credentials never logged or exposed in responses
- API key last_used_at updated for tracking (helps detect compromised keys)

**Performance Considerations**:
- API key validation adds ~50-100ms per request (Supabase query + decryption)
- Connection pooling via httpx reduces Supabase query overhead
- Consider Redis cache for API key → org_id mapping (future optimization)

**Alternatives Considered**:
- **Supabase Auth JWT for MCP tools**: Rejected - Claude Desktop needs static API keys, not session tokens
- **Direct PostgreSQL connection**: Rejected - Supabase client handles auth/RLS/pooling automatically
- **GraphQL API**: Rejected - REST API is simpler, Supabase auto-generates REST from schema

**Rationale**: supabase-py provides seamless integration with FastAPI, handles authentication, and enables RLS bypass for service-level operations.

---

## R7: Multi-Tenant Testing Strategies (RLS Enforcement Verification)

### Decision

Implement **multi-tenant isolation tests** to verify RLS policies prevent cross-organization data access. Use test fixtures to create multiple organizations and verify queries return only organization-scoped data.

### Research Findings

**Multi-Tenant Test Pattern**:
```python
# tests/integration/test_supabase_rls.py
import pytest
from src.services.supabase_client import get_supabase_client
from supabase import Client

@pytest.fixture
async def setup_test_orgs(supabase: Client):
    """Create test organizations and users"""
    # Create Org A
    org_a = supabase.table('organizations').insert({
        'name': 'Test Org A',
        'owner_user_id': 'user_a_id'
    }).execute().data[0]

    # Create Org B
    org_b = supabase.table('organizations').insert({
        'name': 'Test Org B',
        'owner_user_id': 'user_b_id'
    }).execute().data[0]

    # Add API keys for each org
    api_key_a = supabase.table('api_keys').insert({
        'organization_id': org_a['id'],
        'key_hash': 'hash_a',
        'is_active': True
    }).execute().data[0]

    api_key_b = supabase.table('api_keys').insert({
        'organization_id': org_b['id'],
        'key_hash': 'hash_b',
        'is_active': True
    }).execute().data[0]

    yield {
        'org_a': org_a,
        'org_b': org_b,
        'api_key_a': api_key_a,
        'api_key_b': api_key_b
    }

    # Cleanup
    supabase.table('api_keys').delete().eq('organization_id', org_a['id']).execute()
    supabase.table('api_keys').delete().eq('organization_id', org_b['id']).execute()
    supabase.table('organizations').delete().eq('id', org_a['id']).execute()
    supabase.table('organizations').delete().eq('id', org_b['id']).execute()

@pytest.mark.asyncio
async def test_rls_prevents_cross_org_access(setup_test_orgs):
    """Verify RLS policies prevent Org A from accessing Org B's data"""
    supabase = get_supabase_client()
    orgs = await setup_test_orgs

    # Authenticate as Org A user (simulate RLS context)
    supabase.auth.set_session(access_token='user_a_token')

    # Query API keys - should only see Org A's keys
    result = supabase.table('api_keys').select('*').execute()

    assert len(result.data) == 1, "Should only see Org A's API key"
    assert result.data[0]['organization_id'] == orgs['org_a']['id']
    assert result.data[0]['organization_id'] != orgs['org_b']['id']

@pytest.mark.asyncio
async def test_concurrent_org_requests(setup_test_orgs):
    """Verify concurrent requests from different orgs don't leak data"""
    import asyncio
    from httpx import AsyncClient

    orgs = await setup_test_orgs

    async def fetch_properties_for_org(api_key: str):
        async with AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/api/properties",
                headers={"X-API-Key": api_key}
            )
            return response.json()

    # Make concurrent requests from both orgs
    results = await asyncio.gather(
        fetch_properties_for_org('api_key_a_value'),
        fetch_properties_for_org('api_key_b_value')
    )

    # Verify each org only sees their own data
    assert results[0]['org_id'] == orgs['org_a']['id']
    assert results[1]['org_id'] == orgs['org_b']['id']
    assert results[0] != results[1], "Orgs should see different data"

# tests/e2e/test_onboarding_flow.py
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_multi_org_onboarding():
    """E2E test: Two users sign up and verify data isolation"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        # User A signup
        page_a = await browser.new_page()
        await page_a.goto('http://localhost:3000/signup')
        await page_a.fill('input[name="email"]', 'usera@example.com')
        await page_a.fill('input[name="password"]', 'password123')
        await page_a.click('button[type="submit"]')
        await page_a.wait_for_url('**/dashboard')

        # User A connects Hostaway account
        await page_a.click('text=Connect Hostaway')
        await page_a.fill('input[name="account_id"]', 'ACC_A')
        await page_a.fill('input[name="secret_key"]', 'SECRET_A')
        await page_a.click('button[type="submit"]')

        # User A generates API key
        await page_a.click('text=Generate API Key')
        api_key_a = await page_a.locator('[data-testid="api-key-display"]').text_content()

        # User B signup (in parallel)
        page_b = await browser.new_page()
        await page_b.goto('http://localhost:3000/signup')
        await page_b.fill('input[name="email"]', 'userb@example.com')
        await page_b.fill('input[name="password"]', 'password123')
        await page_b.click('button[type="submit"]')
        await page_b.wait_for_url('**/dashboard')

        # User B connects different Hostaway account
        await page_b.click('text=Connect Hostaway')
        await page_b.fill('input[name="account_id"]', 'ACC_B')
        await page_b.fill('input[name="secret_key"]', 'SECRET_B')
        await page_b.click('button[type="submit"]')

        # Verify User A cannot see User B's credentials in dashboard
        await page_a.goto('http://localhost:3000/dashboard/settings')
        hostaway_account_a = await page_a.locator('[data-testid="hostaway-account"]').text_content()
        assert 'ACC_A' in hostaway_account_a
        assert 'ACC_B' not in hostaway_account_a

        await browser.close()
```

**Key Insights**:
1. **RLS context simulation**: Use `supabase.auth.set_session()` to simulate authenticated user in tests
2. **Concurrent isolation tests**: Verify parallel requests don't leak data between orgs
3. **E2E onboarding flow**: Playwright tests verify UI-level isolation (user A can't see user B's data)
4. **Cleanup fixtures**: Always clean up test data to avoid polluting database

**Test Categories**:
- **Unit**: RLS policy logic, API key hashing, credential encryption/decryption
- **Integration**: Supabase queries with RLS enabled, FastAPI-Supabase data flow
- **E2E**: Full user journey from signup → API key generation → MCP tool usage
- **Load**: 1000 concurrent MCP requests across 100 orgs (verify no data leakage under load)

**Performance Testing**:
```python
@pytest.mark.asyncio
async def test_concurrent_load_no_leakage():
    """Verify 1000 concurrent requests across 100 orgs have no data leakage"""
    import asyncio

    # Create 100 test orgs with API keys
    orgs = await create_test_orgs(count=100)

    async def make_request(api_key: str, expected_org_id: int):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/api/properties",
                headers={"X-API-Key": api_key}
            )
            data = response.json()
            assert data['org_id'] == expected_org_id, f"Data leaked to wrong org!"
            return data

    # Make 10 requests per org (1000 total)
    tasks = []
    for org in orgs:
        for _ in range(10):
            tasks.append(make_request(org['api_key'], org['org_id']))

    # Run concurrently
    results = await asyncio.gather(*tasks)

    # Verify all requests returned correct org data
    assert len(results) == 1000
    assert all(r['org_id'] in [o['org_id'] for o in orgs] for r in results)
```

**Alternatives Considered**:
- **Manual testing only**: Rejected - RLS policies too critical to rely on manual verification
- **Mocked RLS tests**: Rejected - must test against real Supabase instance to verify policies work
- **Production testing**: Rejected - multi-tenant bugs in production = data breach, must test in staging

**Rationale**: Automated multi-tenant isolation tests provide confidence that RLS policies prevent data leakage under all conditions.

---

## Research Summary

All unknowns from Technical Context have been resolved:

| Unknown | Decision | Key Insight |
|---------|----------|-------------|
| **R1: RLS patterns** | Use subquery-based policies with auth.uid() | Database-enforced isolation, zero application complexity |
| **R2: Vault encryption** | pgsodium.crypto_secretbox with HSM-backed keys | Compliance-ready encryption with zero operational overhead |
| **R3: Next.js Auth** | @supabase/ssr with Server Components | Seamless auth, automatic RLS enforcement, no boilerplate |
| **R4: Stripe billing** | Quantity-based subscriptions with proration | Fair billing, automatic proration, transparent pricing |
| **R5: Edge Functions** | Supabase Edge Functions for webhooks | Serverless, secure, native database integration |
| **R6: FastAPI integration** | supabase-py with service role key | RLS bypass for auth, dependency injection pattern |
| **R7: Testing strategy** | RLS enforcement tests + E2E isolation tests | Automated verification of multi-tenant isolation |

**All research complete. Ready for Phase 1: Design (data-model.md, contracts/, quickstart.md).**
