-- Drop the recursive SELECT policy on organization_members
-- The "Owners view members" policy causes infinite recursion because it checks
-- organization_members while trying to SELECT from organization_members

DROP POLICY IF EXISTS "Owners view members" ON organization_members;

-- The "Users see own memberships" policy is sufficient for users to see their own membership
-- Owners can already see all members via UPDATE/DELETE policies when needed
