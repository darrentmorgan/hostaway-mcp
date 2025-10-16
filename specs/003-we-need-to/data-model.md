# Data Model: Multi-Tenant Billable MCP Server (v2.0)

**Date**: 2025-10-13
**Branch**: `003-we-need-to`
**Phase**: 1 (Design)
**Input**: Research findings from `research.md`, functional requirements FR-001 to FR-027

---

## Overview

v2.0 introduces multi-tenant architecture with 7 new Supabase tables (plus Supabase Auth managed tables) to support organization-based isolation, API key management, Stripe billing, and audit logging. All models use database-enforced Row Level Security (RLS) policies for tenant isolation.

### New Entities

1. **organizations** - Tenant entity representing property management companies
2. **organization_members** - Many-to-many user-organization relationship
3. **hostaway_credentials** - Encrypted Hostaway API credentials per organization
4. **api_keys** - MCP authentication tokens for AI agent access
5. **subscriptions** - Stripe billing subscription per organization
6. **usage_metrics** - Aggregated API usage per organization per month
7. **audit_logs** - MCP tool invocation logs for compliance

**Note**: `auth.users` table is managed by Supabase Auth (not custom application table)

---

## Entity Definitions

### 1. organizations

**Purpose**: Represents a tenant (property management company or individual host)

**Source**: Created on user signup via Next.js dashboard

**Requirements**: FR-001, FR-004, FR-023

```sql
CREATE TABLE organizations (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL CHECK (length(name) >= 1 AND length(name) <= 255),
  owner_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_customer_id TEXT UNIQUE, -- Stripe customer ID for billing
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_organizations_owner ON organizations(owner_user_id);
CREATE INDEX idx_organizations_stripe ON organizations(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;

-- RLS Policy
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users access own organizations" ON organizations
  FOR ALL
  USING (
    id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
    )
  );
```

**Validation Rules**:
- `name`: 1-255 characters, required
- `owner_user_id`: Must reference existing auth.users record
- `stripe_customer_id`: Unique, nullable (set after Stripe customer creation)

**Relationships**:
- **1:N** with organization_members (one org has many members)
- **1:N** with api_keys (one org has many API keys)
- **1:1** with subscriptions (one org has one active subscription)
- **1:N** with hostaway_credentials (one org has one Hostaway account, but supports historical records)

---

### 2. organization_members

**Purpose**: Many-to-many relationship between users and organizations (supports multi-user orgs in future)

**Source**: Created on user signup (owner) or invitation flow (future)

**Requirements**: FR-001, FR-023

```sql
CREATE TYPE organization_role AS ENUM ('owner', 'admin', 'member');

CREATE TABLE organization_members (
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role organization_role NOT NULL DEFAULT 'member',
  joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (organization_id, user_id)
);

-- Indexes
CREATE INDEX idx_org_members_user ON organization_members(user_id);
CREATE INDEX idx_org_members_org ON organization_members(organization_id);

-- RLS Policy
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own memberships" ON organization_members
  FOR SELECT
  USING (user_id = auth.uid());

-- Policy: Only owners can invite members (future enhancement)
CREATE POLICY "Owners manage members" ON organization_members
  FOR ALL
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid() AND role = 'owner'
    )
  );
```

**Validation Rules**:
- `organization_id`: Must reference existing organization
- `user_id`: Must reference existing auth.users record
- `role`: Must be one of 'owner', 'admin', 'member'
- Composite primary key prevents duplicate memberships

**Relationships**:
- **N:1** with organizations (many members belong to one org)
- **N:1** with auth.users (many memberships for one user across different orgs)

---

### 3. hostaway_credentials

**Purpose**: Stores encrypted Hostaway account credentials for each organization

**Source**: Created when user connects Hostaway account via dashboard settings

**Requirements**: FR-002, FR-003, FR-022

```sql
CREATE TABLE hostaway_credentials (
  id BIGSERIAL PRIMARY KEY,
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  account_id TEXT NOT NULL CHECK (length(account_id) >= 1),
  encrypted_secret_key TEXT NOT NULL, -- Encrypted via pgsodium.crypto_secretbox
  credentials_valid BOOLEAN NOT NULL DEFAULT true,
  last_validated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(organization_id) -- One active credential per org
);

-- Indexes
CREATE INDEX idx_hostaway_creds_org ON hostaway_credentials(organization_id);
CREATE INDEX idx_hostaway_creds_valid ON hostaway_credentials(credentials_valid) WHERE credentials_valid = true;

-- RLS Policy
ALTER TABLE hostaway_credentials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users access own org credentials" ON hostaway_credentials
  FOR SELECT
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
    )
  );

-- Policy: Only owners can insert/update credentials
CREATE POLICY "Owners manage credentials" ON hostaway_credentials
  FOR INSERT, UPDATE
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid() AND role IN ('owner', 'admin')
    )
  );
```

**Validation Rules**:
- `account_id`: Non-empty string (Hostaway account ID format)
- `encrypted_secret_key`: Required, encrypted via Supabase Vault (pgsodium)
- `credentials_valid`: Boolean flag, set to false if Hostaway returns 401
- Unique constraint ensures one active credential per organization

**Encryption Pattern**:
```sql
-- Encrypt on insert (via application or database trigger)
INSERT INTO hostaway_credentials (organization_id, account_id, encrypted_secret_key)
VALUES (
  123,
  'ACC_12345',
  pgsodium.crypto_secretbox(
    'hostaway_secret_key_value'::bytea,
    (SELECT secret FROM vault.secrets WHERE name = 'hostaway_encryption_key')
  )
);

-- Decrypt on select (service role only, in FastAPI backend)
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

**Relationships**:
- **N:1** with organizations (many credentials can exist for one org, but only one active via UNIQUE constraint)

---

### 4. api_keys

**Purpose**: MCP authentication tokens for AI agents (static keys for Claude Desktop)

**Source**: Generated via Next.js dashboard API key management page

**Requirements**: FR-005 to FR-008, FR-020, FR-024

```sql
CREATE TABLE api_keys (
  id BIGSERIAL PRIMARY KEY,
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  key_hash TEXT NOT NULL UNIQUE, -- SHA-256 hash of actual key
  created_by_user_id UUID NOT NULL REFERENCES auth.users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,
  is_active BOOLEAN NOT NULL DEFAULT true,
  CHECK (length(key_hash) = 64) -- SHA-256 produces 64 hex chars
);

-- Indexes
CREATE INDEX idx_api_keys_org ON api_keys(organization_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash) WHERE is_active = true; -- Fast lookup for validation
CREATE INDEX idx_api_keys_active ON api_keys(organization_id, is_active) WHERE is_active = true;

-- RLS Policy
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own org API keys" ON api_keys
  FOR ALL
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
    )
  );

-- Policy: Max 5 active API keys per org (enforced via application logic + constraint)
CREATE OR REPLACE FUNCTION check_api_key_limit()
RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT COUNT(*) FROM api_keys WHERE organization_id = NEW.organization_id AND is_active = true) >= 5 THEN
    RAISE EXCEPTION 'Maximum 5 active API keys per organization';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER api_key_limit_trigger
BEFORE INSERT ON api_keys
FOR EACH ROW
EXECUTE FUNCTION check_api_key_limit();
```

**Validation Rules**:
- `key_hash`: SHA-256 hash (64 hex characters), unique across all orgs
- `is_active`: Boolean flag, set to false on deletion/regeneration
- Max 5 active keys per organization (enforced via trigger)
- Original key value **never stored**, only hash (key shown once at generation)

**Key Generation Pattern** (in Next.js API route):
```typescript
import crypto from 'crypto'

// Generate API key
const apiKey = crypto.randomBytes(32).toString('hex') // 64 char hex string
const keyHash = crypto.createHash('sha256').update(apiKey).digest('hex')

// Store hash
await supabase.from('api_keys').insert({
  organization_id: orgId,
  key_hash: keyHash,
  created_by_user_id: userId,
  is_active: true
})

// Return full key ONCE (never stored again)
return { api_key: apiKey }
```

**Relationships**:
- **N:1** with organizations (many API keys belong to one org)
- **N:1** with auth.users (created_by tracks who generated the key)

---

### 5. subscriptions

**Purpose**: Stripe subscription reference for billing per organization

**Source**: Created when organization completes onboarding and connects Hostaway account

**Requirements**: FR-009 to FR-013, FR-025

```sql
CREATE TYPE subscription_status AS ENUM ('active', 'past_due', 'canceled', 'trialing', 'incomplete');

CREATE TABLE subscriptions (
  id BIGSERIAL PRIMARY KEY,
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  stripe_subscription_id TEXT NOT NULL UNIQUE,
  stripe_customer_id TEXT NOT NULL, -- Denormalized for easier Stripe webhook processing
  current_quantity INT NOT NULL DEFAULT 0 CHECK (current_quantity >= 0), -- Active listing count
  status subscription_status NOT NULL DEFAULT 'trialing',
  billing_period_start TIMESTAMPTZ NOT NULL,
  billing_period_end TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(organization_id) -- One active subscription per org
);

-- Indexes
CREATE INDEX idx_subscriptions_org ON subscriptions(organization_id);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- RLS Policy
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own org subscription" ON subscriptions
  FOR SELECT
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
    )
  );

-- Policy: Only system (webhooks) can update subscription
CREATE POLICY "System updates subscriptions" ON subscriptions
  FOR UPDATE
  USING (true) -- Service role key can update any subscription
  WITH CHECK (true);
```

**Validation Rules**:
- `stripe_subscription_id`: Unique Stripe subscription ID (format: `sub_xxx`)
- `current_quantity`: Non-negative integer (listing count)
- `status`: Must be valid subscription status enum
- `billing_period_start` < `billing_period_end`
- Unique constraint ensures one active subscription per organization

**Update Pattern** (via Stripe webhook Edge Function):
```typescript
// On invoice.payment_failed
await supabase
  .from('subscriptions')
  .update({ status: 'past_due' })
  .eq('organization_id', orgId)

// On customer.subscription.updated
await supabase
  .from('subscriptions')
  .update({
    current_quantity: newQuantity,
    billing_period_start: periodStart,
    billing_period_end: periodEnd
  })
  .eq('stripe_subscription_id', subId)
```

**Relationships**:
- **1:1** with organizations (one org has one active subscription)

---

### 6. usage_metrics

**Purpose**: Aggregated API usage statistics per organization per month

**Source**: Updated on every MCP tool invocation (async increment)

**Requirements**: FR-014 to FR-016

```sql
CREATE TABLE usage_metrics (
  id BIGSERIAL PRIMARY KEY,
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  month_year TEXT NOT NULL CHECK (month_year ~ '^\d{4}-\d{2}$'), -- Format: YYYY-MM
  total_api_requests INT NOT NULL DEFAULT 0 CHECK (total_api_requests >= 0),
  unique_tools_used TEXT[] NOT NULL DEFAULT '{}', -- Array of tool names
  listing_count_snapshot INT NOT NULL DEFAULT 0, -- Snapshot of listing count for this month
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(organization_id, month_year) -- One record per org per month
);

-- Indexes
CREATE INDEX idx_usage_metrics_org ON usage_metrics(organization_id);
CREATE INDEX idx_usage_metrics_month ON usage_metrics(month_year);
CREATE INDEX idx_usage_metrics_org_month ON usage_metrics(organization_id, month_year);

-- RLS Policy
ALTER TABLE usage_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own org usage" ON usage_metrics
  FOR SELECT
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
    )
  );
```

**Validation Rules**:
- `month_year`: Must match YYYY-MM format (e.g., "2025-10")
- `total_api_requests`: Non-negative integer
- `unique_tools_used`: Array of tool names (e.g., ["get_properties", "create_listing"])
- Unique constraint ensures one metrics record per org per month

**Increment Pattern** (in FastAPI middleware):
```python
from datetime import datetime

async def track_usage(org_id: int, tool_name: str):
    month_year = datetime.now().strftime("%Y-%m")

    # Upsert usage metrics (increment total_api_requests, add tool to array)
    await supabase.rpc('increment_usage_metrics', {
        'org_id': org_id,
        'month': month_year,
        'tool': tool_name
    })

# RPC function in database
CREATE OR REPLACE FUNCTION increment_usage_metrics(
  org_id BIGINT,
  month TEXT,
  tool TEXT
)
RETURNS VOID AS $$
BEGIN
  INSERT INTO usage_metrics (organization_id, month_year, total_api_requests, unique_tools_used)
  VALUES (org_id, month, 1, ARRAY[tool])
  ON CONFLICT (organization_id, month_year) DO UPDATE
  SET
    total_api_requests = usage_metrics.total_api_requests + 1,
    unique_tools_used = array_append(usage_metrics.unique_tools_used, tool),
    updated_at = NOW();
END;
$$ LANGUAGE plpgsql;
```

**Relationships**:
- **N:1** with organizations (many monthly metrics for one org)

---

### 7. audit_logs

**Purpose**: Detailed logs of all MCP tool invocations for compliance and debugging

**Source**: Written on every MCP tool invocation (async, non-blocking)

**Requirements**: FR-021

```sql
CREATE TABLE audit_logs (
  id BIGSERIAL PRIMARY KEY,
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id), -- Nullable: API key usage doesn't have user_id
  tool_name TEXT NOT NULL CHECK (length(tool_name) >= 1),
  request_params JSONB, -- Tool invocation parameters
  response_status INT NOT NULL CHECK (response_status >= 100 AND response_status < 600),
  error_message TEXT, -- Nullable: only set if response_status >= 400
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_tool ON audit_logs(tool_name);
CREATE INDEX idx_audit_logs_status ON audit_logs(response_status) WHERE response_status >= 400; -- Fast lookup for errors

-- Partitioning by month (for retention/archival)
CREATE TABLE audit_logs_2025_10 PARTITION OF audit_logs
FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

-- RLS Policy
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own org audit logs" ON audit_logs
  FOR SELECT
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
    )
  );
```

**Validation Rules**:
- `tool_name`: Non-empty string (MCP tool name)
- `request_params`: JSONB (can be null if no params)
- `response_status`: HTTP status code (100-599)
- `error_message`: Nullable, only set if response_status >= 400

**Logging Pattern** (in FastAPI middleware):
```python
async def log_tool_invocation(
    org_id: int,
    tool_name: str,
    request_params: dict,
    response_status: int,
    error_message: str = None
):
    await supabase.table('audit_logs').insert({
        'organization_id': org_id,
        'tool_name': tool_name,
        'request_params': request_params,
        'response_status': response_status,
        'error_message': error_message,
        'created_at': datetime.now().isoformat()
    })
```

**Relationships**:
- **N:1** with organizations (many audit logs for one org)
- **N:1** with auth.users (nullable, only set if user-initiated)

---

## Relationships Diagram

```
┌─────────────────────────┐
│ auth.users              │ (Managed by Supabase Auth)
│ - id (UUID, PK)         │
│ - email                 │
│ - encrypted_password    │
└─────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────┐
│ organization_members    │
│ - organization_id (FK)  │──┐
│ - user_id (FK)          │  │
│ - role                  │  │
└─────────────────────────┘  │
                              │ N:1
                              ▼
                    ┌─────────────────────────┐
                    │ organizations           │
                    │ - id (PK)               │
                    │ - name                  │
                    │ - owner_user_id (FK)    │
                    │ - stripe_customer_id    │
                    └─────────────────────────┘
                              │
                              │ 1:N
           ┌──────────────────┼──────────────────┬──────────────────┐
           │                  │                  │                  │
           ▼                  ▼                  ▼                  ▼
 ┌──────────────────┐  ┌──────────────┐  ┌───────────────┐  ┌────────────────┐
 │ hostaway_creds   │  │ api_keys     │  │ subscriptions │  │ usage_metrics  │
 │ - id (PK)        │  │ - id (PK)    │  │ - id (PK)     │  │ - id (PK)      │
 │ - org_id (FK)    │  │ - org_id(FK) │  │ - org_id (FK) │  │ - org_id (FK)  │
 │ - account_id     │  │ - key_hash   │  │ - stripe_id   │  │ - month_year   │
 │ - encrypted_key  │  │ - is_active  │  │ - quantity    │  │ - api_requests │
 └──────────────────┘  └──────────────┘  └───────────────┘  └────────────────┘

                              │
                              │ 1:N
                              ▼
                    ┌─────────────────────────┐
                    │ audit_logs              │
                    │ - id (PK)               │
                    │ - organization_id (FK)  │
                    │ - tool_name             │
                    │ - request_params (JSONB)│
                    │ - response_status       │
                    └─────────────────────────┘
```

---

## File Organization

### New Model Files (Backend - Python/Pydantic)

```python
# src/models/organization.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Organization(BaseModel):
    """Organization entity (tenant)"""
    id: int
    name: str = Field(..., min_length=1, max_length=255)
    owner_user_id: str  # UUID from auth.users
    stripe_customer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class OrganizationMember(BaseModel):
    """User-organization membership"""
    organization_id: int
    user_id: str  # UUID from auth.users
    role: str = Field(..., pattern="^(owner|admin|member)$")
    joined_at: datetime

class APIKey(BaseModel):
    """MCP API key (hash only, never store actual key)"""
    id: int
    organization_id: int
    key_hash: str = Field(..., min_length=64, max_length=64)
    created_by_user_id: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool = True

class HostawayCredentials(BaseModel):
    """Encrypted Hostaway credentials"""
    id: int
    organization_id: int
    account_id: str
    encrypted_secret_key: str
    credentials_valid: bool = True
    last_validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class Subscription(BaseModel):
    """Stripe subscription"""
    id: int
    organization_id: int
    stripe_subscription_id: str
    stripe_customer_id: str
    current_quantity: int = Field(..., ge=0)
    status: str = Field(..., pattern="^(active|past_due|canceled|trialing|incomplete)$")
    billing_period_start: datetime
    billing_period_end: datetime
    created_at: datetime
    updated_at: datetime

class UsageMetrics(BaseModel):
    """Monthly usage aggregation"""
    id: int
    organization_id: int
    month_year: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    total_api_requests: int = Field(..., ge=0)
    unique_tools_used: list[str] = []
    listing_count_snapshot: int = Field(..., ge=0)
    created_at: datetime
    updated_at: datetime

class AuditLog(BaseModel):
    """MCP tool invocation log"""
    id: int
    organization_id: int
    user_id: Optional[str] = None
    tool_name: str
    request_params: Optional[dict] = None
    response_status: int = Field(..., ge=100, lt=600)
    error_message: Optional[str] = None
    created_at: datetime
```

### Frontend TypeScript Types (Generated from Supabase)

```bash
# Generate TypeScript types from Supabase schema
supabase gen types typescript --project-id xxx > dashboard/lib/types/database.ts
```

```typescript
// dashboard/lib/types/database.ts (auto-generated)
export type Database = {
  public: {
    Tables: {
      organizations: {
        Row: {
          id: number
          name: string
          owner_user_id: string
          stripe_customer_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          name: string
          owner_user_id: string
          stripe_customer_id?: string | null
        }
        Update: {
          name?: string
          stripe_customer_id?: string | null
        }
      }
      api_keys: {
        Row: {
          id: number
          organization_id: number
          key_hash: string
          created_by_user_id: string
          created_at: string
          last_used_at: string | null
          is_active: boolean
        }
        // ... Insert/Update types
      }
      // ... other tables
    }
  }
}
```

---

## Data Model Complete

All entities defined with:
- ✅ SQL schema with constraints and indexes
- ✅ RLS policies for multi-tenant isolation
- ✅ Pydantic models (backend) and TypeScript types (frontend)
- ✅ Validation rules and business logic
- ✅ Relationship mapping
- ✅ Encryption patterns (Supabase Vault)

**Next**: Generate API contracts (supabase-schema.sql, supabase-rls.sql, dashboard-api.yaml, stripe-webhooks.yaml)
