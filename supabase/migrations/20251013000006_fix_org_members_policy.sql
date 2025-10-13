-- Fix infinite recursion in organization_members RLS policy
-- Drop the problematic recursive policy that checks organization_members while inserting into it
DROP POLICY IF EXISTS "Owners manage members" ON organization_members;

-- Create separate policies that don't cause recursion

-- Allow users to insert themselves as members during signup (no recursion)
CREATE POLICY "Users can create own membership" ON organization_members
  FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- Allow owners to view all members in their organization
CREATE POLICY "Owners view members" ON organization_members
  FOR SELECT
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid() AND role = 'owner'
    )
  );

-- Allow owners to update other members (after initial insert, no recursion)
CREATE POLICY "Owners manage other members" ON organization_members
  FOR UPDATE
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid() AND role = 'owner'
    )
  );

-- Allow owners to delete members
CREATE POLICY "Owners delete members" ON organization_members
  FOR DELETE
  USING (
    organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid() AND role = 'owner'
    )
  );
