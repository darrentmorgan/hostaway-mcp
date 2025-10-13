-- Fix organizations RLS policy to prevent infinite recursion
-- The "Users access own organizations" policy was FOR ALL (including INSERT)
-- which caused recursion. We need to exclude INSERT from this policy.

-- Drop the problematic ALL policy
DROP POLICY IF EXISTS "Users access own organizations" ON organizations;

-- Recreate it for SELECT, UPDATE, DELETE only (no INSERT)
CREATE POLICY "Users access own organizations" ON organizations
  FOR SELECT
  USING (
    id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
    )
  );

-- Add UPDATE and DELETE policies separately
CREATE POLICY "Users update own organizations" ON organizations
  FOR UPDATE
  USING (
    id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid() AND role = 'owner'
    )
  );

CREATE POLICY "Users delete own organizations" ON organizations
  FOR DELETE
  USING (
    id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid() AND role = 'owner'
    )
  );

-- Note: INSERT policy "Users create own organizations" already exists from migration 005
