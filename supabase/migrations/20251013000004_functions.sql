-- Migration: 20251013_004_functions.sql
-- Purpose: Create RPC functions and triggers for usage tracking and API key limits
-- Author: Claude Code
-- Date: 2025-10-13

-- ====================================================================
-- 1. increment_usage_metrics RPC Function
-- ====================================================================
-- Purpose: Atomic usage tracking for MCP tool invocations
-- Called from backend middleware on every API request

CREATE OR REPLACE FUNCTION increment_usage_metrics(
  org_id BIGINT,
  month TEXT,
  tool TEXT
)
RETURNS VOID AS $$
BEGIN
  -- Upsert usage metrics for the organization and month
  -- If record exists, increment counters; if not, create new record
  INSERT INTO usage_metrics (
    organization_id,
    month_year,
    total_api_requests,
    unique_tools_used,
    updated_at
  )
  VALUES (
    org_id,
    month,
    1,
    ARRAY[tool],
    NOW()
  )
  ON CONFLICT (organization_id, month_year) DO UPDATE
  SET
    total_api_requests = usage_metrics.total_api_requests + 1,
    unique_tools_used = CASE
      WHEN tool = ANY(usage_metrics.unique_tools_used) THEN usage_metrics.unique_tools_used
      ELSE array_append(usage_metrics.unique_tools_used, tool)
    END,
    updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION increment_usage_metrics(BIGINT, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION increment_usage_metrics(BIGINT, TEXT, TEXT) TO service_role;

-- ====================================================================
-- 2. check_api_key_limit Trigger Function
-- ====================================================================
-- Purpose: Enforce max 5 active API keys per organization
-- Triggered before INSERT on api_keys table

CREATE OR REPLACE FUNCTION check_api_key_limit()
RETURNS TRIGGER AS $$
DECLARE
  active_key_count INT;
BEGIN
  -- Count active API keys for this organization
  SELECT COUNT(*)
  INTO active_key_count
  FROM api_keys
  WHERE organization_id = NEW.organization_id
    AND is_active = true;

  -- Enforce limit
  IF active_key_count >= 5 THEN
    RAISE EXCEPTION 'Maximum 5 active API keys per organization. Please deactivate an existing key before creating a new one.'
      USING ERRCODE = 'check_violation',
            HINT = 'Deactivate unused API keys in the dashboard settings.';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- 3. Attach Trigger to api_keys Table
-- ====================================================================
-- Trigger fires before INSERT to check key limit

CREATE TRIGGER api_key_limit_trigger
BEFORE INSERT ON api_keys
FOR EACH ROW
EXECUTE FUNCTION check_api_key_limit();

-- ====================================================================
-- 4. update_updated_at_timestamp Function
-- ====================================================================
-- Purpose: Automatically update updated_at column on row modification
-- Generic trigger function for any table with updated_at column

CREATE OR REPLACE FUNCTION update_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- 5. Attach update_updated_at Triggers
-- ====================================================================
-- Automatically update updated_at on UPDATE for relevant tables

CREATE TRIGGER update_organizations_timestamp
BEFORE UPDATE ON organizations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_timestamp();

CREATE TRIGGER update_hostaway_credentials_timestamp
BEFORE UPDATE ON hostaway_credentials
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_timestamp();

CREATE TRIGGER update_subscriptions_timestamp
BEFORE UPDATE ON subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_timestamp();

CREATE TRIGGER update_usage_metrics_timestamp
BEFORE UPDATE ON usage_metrics
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_timestamp();

-- ====================================================================
-- 6. get_organization_by_api_key RPC Function
-- ====================================================================
-- Purpose: Retrieve organization context from API key hash
-- Called from backend middleware on every authenticated MCP request

CREATE OR REPLACE FUNCTION get_organization_by_api_key(
  key_hash_param TEXT
)
RETURNS TABLE (
  organization_id BIGINT,
  organization_name TEXT,
  hostaway_account_id TEXT,
  hostaway_secret_key TEXT,
  credentials_valid BOOLEAN
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    o.id AS organization_id,
    o.name AS organization_name,
    hc.account_id AS hostaway_account_id,
    decrypt_hostaway_credential(hc.encrypted_secret_key) AS hostaway_secret_key,
    hc.credentials_valid
  FROM api_keys ak
  JOIN organizations o ON ak.organization_id = o.id
  LEFT JOIN hostaway_credentials hc ON o.id = hc.organization_id
  WHERE ak.key_hash = key_hash_param
    AND ak.is_active = true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to service role only (backend use only)
GRANT EXECUTE ON FUNCTION get_organization_by_api_key(TEXT) TO service_role;

-- ====================================================================
-- 7. update_api_key_last_used RPC Function
-- ====================================================================
-- Purpose: Update last_used_at timestamp when API key is used
-- Called from backend middleware on successful authentication

CREATE OR REPLACE FUNCTION update_api_key_last_used(
  key_hash_param TEXT
)
RETURNS VOID AS $$
BEGIN
  UPDATE api_keys
  SET last_used_at = NOW()
  WHERE key_hash = key_hash_param
    AND is_active = true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to service role only (backend use only)
GRANT EXECUTE ON FUNCTION update_api_key_last_used(TEXT) TO service_role;

-- ====================================================================
-- Migration Complete
-- ====================================================================
-- Functions created:
-- 1. increment_usage_metrics() - Atomic usage tracking
-- 2. check_api_key_limit() - Enforce 5 API key limit
-- 3. update_updated_at_timestamp() - Auto-update timestamps
-- 4. get_organization_by_api_key() - Retrieve org context from API key
-- 5. update_api_key_last_used() - Track API key usage
--
-- Triggers attached:
-- 1. api_key_limit_trigger - Before INSERT on api_keys
-- 2. update_*_timestamp - Before UPDATE on tables with updated_at
