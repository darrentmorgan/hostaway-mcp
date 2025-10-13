-- Seed file for Supabase local development
-- This file runs after migrations with proper permissions

-- Create encryption key in vault for Hostaway credentials
-- This uses pgsodium's vault.create_secret() function which has proper permissions
SELECT vault.create_secret(encode(gen_random_bytes(32), 'base64'), 'hostaway_encryption_key');

-- Verify the key was created
DO $$
DECLARE
    key_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM vault.secrets WHERE name = 'hostaway_encryption_key') INTO key_exists;
    IF key_exists THEN
        RAISE NOTICE 'Vault encryption key "hostaway_encryption_key" created successfully';
    ELSE
        RAISE EXCEPTION 'Failed to create vault encryption key';
    END IF;
END $$;
