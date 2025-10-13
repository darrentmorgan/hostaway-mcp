-- Add Stripe customer ID to organizations table for billing integration
-- This allows linking each organization to their Stripe customer record

ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT;

-- Add index for faster lookups by Stripe customer ID
CREATE INDEX IF NOT EXISTS idx_organizations_stripe_customer_id
ON organizations(stripe_customer_id);

-- Add comment explaining the column
COMMENT ON COLUMN organizations.stripe_customer_id IS
'Stripe customer ID (cus_xxx) for billing operations. Created when organization signs up.';
