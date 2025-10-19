# GitHub Secrets Configuration Contract

**Feature**: Automated CI/CD Pipeline for Hostinger Deployment
**Phase**: 1 - Design & Contracts
**Date**: 2025-10-19

## Overview

This contract defines the structure and validation rules for GitHub repository secrets required for automated deployment. These secrets are configured once in GitHub repository settings and used by the deployment workflow.

## Required Secrets

### SSH Authentication Secrets

#### `SSH_PRIVATE_KEY`
- **Type**: String (multiline)
- **Format**: Ed25519 private key in PEM format
- **Validation**:
  - MUST start with `-----BEGIN OPENSSH PRIVATE KEY-----`
  - MUST end with `-----END OPENSSH PRIVATE KEY-----`
  - MUST be valid Ed25519 key (256-bit)
- **Usage**: Authenticates GitHub Actions runner to Hostinger VPS
- **Security**: Never logged, auto-masked by GitHub Actions
- **Rotation**: Every 90 days (recommended)
- **Example**:
  ```
  -----BEGIN OPENSSH PRIVATE KEY-----
  b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
  [... key content ...]
  -----END OPENSSH PRIVATE KEY-----
  ```

#### `SSH_HOST`
- **Type**: String
- **Format**: IP address or hostname
- **Validation**:
  - MUST be valid IPv4 address (e.g., `72.60.233.157`) OR valid hostname
  - MUST be reachable on port 22 (SSH)
- **Usage**: Target server for deployment
- **Security**: Not sensitive, but auto-masked in logs
- **Example**: `72.60.233.157`

#### `SSH_USERNAME`
- **Type**: String
- **Format**: Unix username
- **Validation**:
  - MUST be valid Unix username (lowercase, alphanumeric, underscore, hyphen)
  - MUST have write permissions to `DEPLOY_PATH`
- **Usage**: SSH login username on Hostinger
- **Security**: Not highly sensitive, but masked in logs
- **Example**: `root`

#### `DEPLOY_PATH`
- **Type**: String
- **Format**: Absolute filesystem path
- **Validation**:
  - MUST start with `/` (absolute path)
  - MUST exist on target server
  - User `SSH_USERNAME` MUST have read/write/execute permissions
- **Usage**: Deployment directory on Hostinger VPS
- **Security**: Not sensitive, but masked in logs
- **Example**: `/opt/hostaway-mcp`

---

### Application Environment Secrets

#### `SUPABASE_URL`
- **Type**: String
- **Format**: HTTPS URL
- **Validation**:
  - MUST start with `https://`
  - MUST be valid Supabase project URL format
  - MUST end with `.supabase.co`
- **Usage**: Supabase API endpoint for database operations
- **Security**: Moderately sensitive, auto-masked in logs
- **Example**: `https://abcdefghijklmnop.supabase.co`

#### `SUPABASE_SERVICE_KEY`
- **Type**: String (JWT token)
- **Format**: Base64-encoded JWT
- **Validation**:
  - MUST be valid JWT format (3 parts separated by `.`)
  - MUST have service role permissions
  - Length approximately 200-300 characters
- **Usage**: Server-side Supabase authentication with elevated privileges
- **Security**: HIGHLY SENSITIVE - never log, auto-masked
- **Rotation**: Every 90 days or on compromise
- **Example**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBh...`

#### `SUPABASE_ANON_KEY`
- **Type**: String (JWT token)
- **Format**: Base64-encoded JWT
- **Validation**:
  - MUST be valid JWT format (3 parts separated by `.`)
  - MUST have anonymous role permissions
  - Length approximately 200-300 characters
- **Usage**: Client-side Supabase authentication with public access
- **Security**: Public key, but masked in logs for consistency
- **Example**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBh...`

#### `HOSTAWAY_ACCOUNT_ID`
- **Type**: String (integer)
- **Format**: Numeric string
- **Validation**:
  - MUST be valid integer
  - MUST match Hostaway account ID
- **Usage**: Hostaway API authentication
- **Security**: Moderately sensitive, auto-masked
- **Example**: `123456`

#### `HOSTAWAY_SECRET_KEY`
- **Type**: String
- **Format**: Alphanumeric string
- **Validation**:
  - MUST be valid Hostaway API secret
  - Length varies (check Hostaway documentation)
- **Usage**: Hostaway API authentication
- **Security**: HIGHLY SENSITIVE - never log, auto-masked
- **Rotation**: On compromise or quarterly
- **Example**: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

---

## Secret Configuration Procedure

### Prerequisites
- GitHub repository admin access
- Hostinger VPS root access
- Supabase project credentials
- Hostaway API credentials

### Configuration Steps

1. **Generate SSH Key Pair** (if not already done):
   ```bash
   ssh-keygen -t ed25519 -C "github-actions-deployment" -f ~/.ssh/hostaway-deploy
   ```

2. **Add Public Key to Hostinger**:
   ```bash
   # On Hostinger VPS
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   cat >> ~/.ssh/authorized_keys <<EOF
   [paste public key from hostaway-deploy.pub]
   EOF
   chmod 600 ~/.ssh/authorized_keys
   ```

3. **Configure GitHub Secrets**:
   - Navigate to: `https://github.com/[OWNER]/[REPO]/settings/secrets/actions`
   - Click "New repository secret" for each secret
   - Paste values exactly as provided (no extra whitespace)
   - Verify each secret is saved (green checkmark appears)

4. **Validation**:
   - Manually trigger workflow using `workflow_dispatch`
   - Check workflow logs for secret masking (values appear as `***`)
   - Verify SSH connection succeeds
   - Confirm .env file created on server with correct values

---

## Secret Validation Rules

### At Configuration Time (Manual)
- All 9 secrets MUST be present before workflow can run
- Secret names MUST match exactly (case-sensitive)
- Secret values MUST pass format validation (see above)
- SSH key MUST match public key on Hostinger server

### At Runtime (Automatic)
- GitHub Actions automatically masks all secret values in logs
- Workflow fails immediately if secrets are undefined
- SSH authentication fails if key is invalid
- Health check fails if environment variables are incorrect

---

## Security Best Practices

### Secret Management
- ✅ Rotate SSH keys every 90 days
- ✅ Rotate API keys on compromise or quarterly
- ✅ Use unique keys for deployments (don't reuse personal keys)
- ✅ Limit secret access to repository admins only
- ✅ Audit secret access via GitHub Actions logs

### What NOT to Do
- ❌ Never commit secrets to repository (even in `.env.example`)
- ❌ Never echo or print secret values in scripts
- ❌ Never share secrets via email or chat
- ❌ Never use the same key for multiple environments
- ❌ Never disable secret masking in GitHub Actions

### Incident Response
If secrets are compromised:
1. Immediately rotate compromised secret in source system (Hostinger, Supabase, Hostaway)
2. Update GitHub repository secret with new value
3. Re-deploy to production to update `.env` file
4. Audit recent workflow runs for unauthorized access
5. Review access logs on Hostinger VPS

---

## Testing Secret Configuration

### Test Procedure
1. Create a test branch
2. Trigger workflow manually using `workflow_dispatch`
3. Verify workflow completes successfully
4. Check logs for:
   - Secret masking (all values show as `***`)
   - Successful SSH connection
   - Successful .env file creation
   - Passing health check
5. SSH to server and verify `.env` file contains correct values

### Expected Outcomes
- ✅ Workflow completes in <10 minutes
- ✅ All secrets masked in logs
- ✅ SSH authentication succeeds
- ✅ .env file created with 600 permissions
- ✅ Health check returns 200 OK
- ✅ Deployment log shows "Deployment successful"

---

## Contract Compliance

This contract satisfies the following requirements:
- **FR-002**: SSH key authentication from GitHub secrets
- **FR-003**: Environment variable transfer from GitHub secrets
- **FR-006**: Secret masking in workflow logs
- **FR-010**: Deployment prevention when secrets missing
- **SC-003**: Zero credential exposure

## References
- GitHub Secrets Documentation: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- GitHub Actions Secret Masking: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#masking-a-value-in-log
- SSH Key Generation: https://goteleport.com/blog/comparing-ssh-keys/
