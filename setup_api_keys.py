#!/usr/bin/env python3
"""Setup api_keys table and insert initial API key."""

from supabase import create_client

# Supabase credentials
SUPABASE_URL = "https://khodniyhethjyomscyjw.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtob2RuaXloZXRoanlvbXNjeWp3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDE5MDA4MCwiZXhwIjoyMDY5NzY2MDgwfQ.58Llsii1gzL9mael0FIVavN90D_K0LNuI4p1v8lscQg"

SQL = """
-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
  organization_id TEXT NOT NULL,
  key_hash TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  created_by_user_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  last_used_at TIMESTAMPTZ,
  is_active BOOLEAN NOT NULL DEFAULT true,
  CHECK (length(key_hash) = 64)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_org ON api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(organization_id, is_active) WHERE is_active = true;

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to api_keys"
  ON api_keys FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Insert API key
INSERT INTO api_keys (key_hash, organization_id, name, is_active)
VALUES (
  '603056d3f247194b36e533c06d2cc7c81b5fa288e9bc9bfa29f45c0d5b01ad46',
  'org_demo_general',
  'Claude Desktop MCP',
  true
) ON CONFLICT (key_hash) DO UPDATE SET is_active = true, updated_at = NOW();
"""

if __name__ == "__main__":
    print("Creating Supabase client...")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    print("Executing SQL...")
    result = supabase.rpc("exec", {"sql": SQL}).execute()

    print("Verifying API key was created...")
    api_keys = (
        supabase.table("api_keys")
        .select("*")
        .eq("key_hash", "603056d3f247194b36e533c06d2cc7c81b5fa288e9bc9bfa29f45c0d5b01ad46")
        .execute()
    )

    if api_keys.data:
        print("✅ API key created successfully:")
        print(f"   ID: {api_keys.data[0]['id']}")
        print(f"   Name: {api_keys.data[0]['name']}")
        print(f"   Active: {api_keys.data[0]['is_active']}")
        print(f"   Created: {api_keys.data[0]['created_at']}")
    else:
        print("❌ API key not found after creation")
