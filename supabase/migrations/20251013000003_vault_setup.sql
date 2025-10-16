-- Migration: 20251013_003_vault_setup.sql
-- Purpose: Enable pgsodium extension and configure Vault for credential encryption
-- Author: Claude Code
-- Date: 2025-10-13

-- ====================================================================
-- 1. Enable pgsodium extension for encryption
-- ====================================================================
-- pgsodium provides cryptographic functions for encrypting sensitive data
CREATE EXTENSION IF NOT EXISTS pgsodium;

-- ====================================================================
-- 2. Create encryption key in Vault
-- ====================================================================
-- IMPORTANT: This key insertion should be done manually via Supabase Dashboard
-- or via service role key to ensure key is securely generated
--
-- The following is a template - DO NOT commit actual key values to git
--
-- To create the encryption key manually:
-- 1. Navigate to Supabase Dashboard > Database > Vault
-- 2. Create new secret with name: 'hostaway_encryption_key'
-- 3. Generate a secure random key (32 bytes recommended)
--
-- Example SQL (execute manually with service role):
-- INSERT INTO vault.secrets (name, secret)
-- VALUES (
--   'hostaway_encryption_key',
--   pgsodium.crypto_secretbox_keygen()
-- );

-- ====================================================================
-- 3. Encryption/Decryption Pattern Documentation
-- ====================================================================
--
-- ENCRYPTING DATA (on insert/update):
-- ---------------------------------
-- INSERT INTO hostaway_credentials (organization_id, account_id, encrypted_secret_key)
-- VALUES (
--   123,
--   'ACC_12345',
--   encode(
--     pgsodium.crypto_secretbox_noncegen() ||
--     pgsodium.crypto_secretbox(
--       'hostaway_secret_key_value'::bytea,
--       pgsodium.crypto_secretbox_noncegen(),
--       (SELECT decrypted_secret FROM vault.decrypted_secrets WHERE name = 'hostaway_encryption_key')
--     ),
--     'base64'
--   )
-- );
--
-- DECRYPTING DATA (on select - service role only):
-- ------------------------------------------------
-- SELECT
--   organization_id,
--   account_id,
--   convert_from(
--     pgsodium.crypto_secretbox_open(
--       decode(substring(encrypted_secret_key from 25), 'base64'),
--       decode(substring(encrypted_secret_key from 1 for 24), 'base64'),
--       (SELECT decrypted_secret FROM vault.decrypted_secrets WHERE name = 'hostaway_encryption_key')
--     ),
--     'UTF8'
--   ) AS secret_key
-- FROM hostaway_credentials
-- WHERE organization_id = 123;
--
-- NOTE: Encryption/decryption should be handled by backend application code
-- using Supabase service role key, NOT directly in client applications

-- ====================================================================
-- 4. Helper Function for Credential Encryption (Optional)
-- ====================================================================
-- Create a helper function for encrypting credentials
-- This can be called from backend application code

CREATE OR REPLACE FUNCTION encrypt_hostaway_credential(
  plain_secret TEXT
)
RETURNS TEXT AS $$
DECLARE
  encryption_key BYTEA;
  nonce BYTEA;
  encrypted BYTEA;
BEGIN
  -- Retrieve encryption key from vault
  SELECT decrypted_secret INTO encryption_key
  FROM vault.decrypted_secrets
  WHERE name = 'hostaway_encryption_key';

  IF encryption_key IS NULL THEN
    RAISE EXCEPTION 'Encryption key not found in vault';
  END IF;

  -- Generate nonce
  nonce := pgsodium.crypto_secretbox_noncegen();

  -- Encrypt the secret
  encrypted := pgsodium.crypto_secretbox(
    plain_secret::bytea,
    nonce,
    encryption_key
  );

  -- Return nonce + encrypted data as base64
  RETURN encode(nonce || encrypted, 'base64');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ====================================================================
-- 5. Helper Function for Credential Decryption (Optional)
-- ====================================================================
-- Create a helper function for decrypting credentials
-- This can be called from backend application code

CREATE OR REPLACE FUNCTION decrypt_hostaway_credential(
  encrypted_secret TEXT
)
RETURNS TEXT AS $$
DECLARE
  encryption_key BYTEA;
  nonce BYTEA;
  encrypted BYTEA;
  decrypted BYTEA;
  full_data BYTEA;
BEGIN
  -- Retrieve encryption key from vault
  SELECT decrypted_secret INTO encryption_key
  FROM vault.decrypted_secrets
  WHERE name = 'hostaway_encryption_key';

  IF encryption_key IS NULL THEN
    RAISE EXCEPTION 'Encryption key not found in vault';
  END IF;

  -- Decode base64 input
  full_data := decode(encrypted_secret, 'base64');

  -- Extract nonce (first 24 bytes) and encrypted data
  nonce := substring(full_data from 1 for 24);
  encrypted := substring(full_data from 25);

  -- Decrypt the secret
  decrypted := pgsodium.crypto_secretbox_open(
    encrypted,
    nonce,
    encryption_key
  );

  IF decrypted IS NULL THEN
    RAISE EXCEPTION 'Decryption failed - invalid key or corrupted data';
  END IF;

  -- Return decrypted text
  RETURN convert_from(decrypted, 'UTF8');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ====================================================================
-- Migration Complete
-- ====================================================================
-- pgsodium extension enabled
-- Helper functions created for encryption/decryption
--
-- NEXT STEPS (Manual):
-- 1. Create encryption key in Supabase Dashboard > Vault
-- 2. Store key name as: 'hostaway_encryption_key'
-- 3. Backend application should use encrypt_hostaway_credential() when storing
-- 4. Backend application should use decrypt_hostaway_credential() when retrieving
