-- Migration: 20251013_001_initial_schema.sql
-- Purpose: Create all 7 core tables for multi-tenant Hostaway MCP server
-- Author: Claude Code
-- Date: 2025-10-13

-- ====================================================================
-- 1. organizations table
-- ====================================================================
-- Purpose: Tenant entity representing property management companies
CREATE TABLE organizations (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL CHECK (length(name) >= 1 AND length(name) <= 255),
  owner_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_customer_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for organizations
CREATE INDEX idx_organizations_owner ON organizations(owner_user_id);
CREATE INDEX idx_organizations_stripe ON organizations(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;

-- ====================================================================
-- 2. organization_members table
-- ====================================================================
-- Purpose: Many-to-many relationship between users and organizations
CREATE TYPE organization_role AS ENUM ('owner', 'admin', 'member');

CREATE TABLE organization_members (
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role organization_role NOT NULL DEFAULT 'member',
  joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (organization_id, user_id)
);

-- Indexes for organization_members
CREATE INDEX idx_org_members_user ON organization_members(user_id);
CREATE INDEX idx_org_members_org ON organization_members(organization_id);

-- ====================================================================
-- 3. hostaway_credentials table
-- ====================================================================
-- Purpose: Stores encrypted Hostaway account credentials for each organization
CREATE TABLE hostaway_credentials (
  id BIGSERIAL PRIMARY KEY,
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  account_id TEXT NOT NULL CHECK (length(account_id) >= 1),
  encrypted_secret_key TEXT NOT NULL,
  credentials_valid BOOLEAN NOT NULL DEFAULT true,
  last_validated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(organization_id)
);

-- Indexes for hostaway_credentials
CREATE INDEX idx_hostaway_creds_org ON hostaway_credentials(organization_id);
CREATE INDEX idx_hostaway_creds_valid ON hostaway_credentials(credentials_valid) WHERE credentials_valid = true;

-- ====================================================================
-- 4. api_keys table
-- ====================================================================
-- Purpose: MCP authentication tokens for AI agents (static keys for Claude Desktop)
CREATE TABLE api_keys (
  id BIGSERIAL PRIMARY KEY,
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  key_hash TEXT NOT NULL UNIQUE,
  created_by_user_id UUID NOT NULL REFERENCES auth.users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,
  is_active BOOLEAN NOT NULL DEFAULT true,
  CHECK (length(key_hash) = 64)
);

-- Indexes for api_keys
CREATE INDEX idx_api_keys_org ON api_keys(organization_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash) WHERE is_active = true;
CREATE INDEX idx_api_keys_active ON api_keys(organization_id, is_active) WHERE is_active = true;

-- ====================================================================
-- 5. subscriptions table
-- ====================================================================
-- Purpose: Stripe subscription reference for billing per organization
CREATE TYPE subscription_status AS ENUM ('active', 'past_due', 'canceled', 'trialing', 'incomplete');

CREATE TABLE subscriptions (
  id BIGSERIAL PRIMARY KEY,
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  stripe_subscription_id TEXT NOT NULL UNIQUE,
  stripe_customer_id TEXT NOT NULL,
  current_quantity INT NOT NULL DEFAULT 0 CHECK (current_quantity >= 0),
  status subscription_status NOT NULL DEFAULT 'trialing',
  billing_period_start TIMESTAMPTZ NOT NULL,
  billing_period_end TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(organization_id)
);

-- Indexes for subscriptions
CREATE INDEX idx_subscriptions_org ON subscriptions(organization_id);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- ====================================================================
-- 6. usage_metrics table
-- ====================================================================
-- Purpose: Aggregated API usage statistics per organization per month
CREATE TABLE usage_metrics (
  id BIGSERIAL PRIMARY KEY,
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  month_year TEXT NOT NULL CHECK (month_year ~ '^\d{4}-\d{2}$'),
  total_api_requests INT NOT NULL DEFAULT 0 CHECK (total_api_requests >= 0),
  unique_tools_used TEXT[] NOT NULL DEFAULT '{}',
  listing_count_snapshot INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(organization_id, month_year)
);

-- Indexes for usage_metrics
CREATE INDEX idx_usage_metrics_org ON usage_metrics(organization_id);
CREATE INDEX idx_usage_metrics_month ON usage_metrics(month_year);
CREATE INDEX idx_usage_metrics_org_month ON usage_metrics(organization_id, month_year);

-- ====================================================================
-- 7. audit_logs table
-- ====================================================================
-- Purpose: Detailed logs of all MCP tool invocations for compliance and debugging
CREATE TABLE audit_logs (
  id BIGSERIAL PRIMARY KEY,
  organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id),
  tool_name TEXT NOT NULL CHECK (length(tool_name) >= 1),
  request_params JSONB,
  response_status INT NOT NULL CHECK (response_status >= 100 AND response_status < 600),
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for audit_logs
CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_tool ON audit_logs(tool_name);
CREATE INDEX idx_audit_logs_status ON audit_logs(response_status) WHERE response_status >= 400;

-- ====================================================================
-- Migration Complete
-- ====================================================================
-- All 7 tables created with constraints, indexes, and foreign keys
-- RLS policies will be added in next migration (20251013_002_rls_policies.sql)
