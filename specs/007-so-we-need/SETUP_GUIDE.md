# CI/CD Pipeline Setup Guide - Manual Steps Required

**Feature**: Automated CI/CD Pipeline for Hostinger Deployment
**Phase 2**: Foundational Prerequisites (Tasks T003-T015)

⚠️ **CRITICAL**: These manual steps MUST be completed before the automated workflow can function.

---

## Step 1: Generate SSH Key Pair (T003)

On your local workstation, generate an Ed25519 SSH key pair:

```bash
# Generate SSH key for GitHub Actions
ssh-keygen -t ed25519 -C "github-actions-hostaway-deployment" -f ~/.ssh/hostaway-deploy

# Press Enter twice to skip passphrase (REQUIRED - GitHub Actions cannot handle passphrases)
```

**Expected Output**:
```
Generating public/private ed25519 key pair.
Enter passphrase (empty for no passphrase): [press Enter]
Enter same passphrase again: [press Enter]
Your identification has been saved in /Users/you/.ssh/hostaway-deploy
Your public key has been saved in /Users/you/.ssh/hostaway-deploy.pub
```

**Result**: Two files created:
- `~/.ssh/hostaway-deploy` - Private key (for GitHub Secrets)
- `~/.ssh/hostaway-deploy.pub` - Public key (for Hostinger)

---

## Step 2: Add Public Key to Hostinger (T004)

1. Display your public key:
   ```bash
   cat ~/.ssh/hostaway-deploy.pub
   ```

2. Copy the entire output (starts with `ssh-ed25519`)

3. SSH to Hostinger VPS:
   ```bash
   ssh root@72.60.233.157
   ```

4. On Hostinger, add the public key:
   ```bash
   # Create .ssh directory if not exists
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh

   # Add public key to authorized_keys
   cat >> ~/.ssh/authorized_keys <<'EOF'
   [PASTE YOUR PUBLIC KEY HERE]
   EOF

   # Secure permissions
   chmod 600 ~/.ssh/authorized_keys

   # Exit Hostinger
   exit
   ```

---

## Step 3: Test SSH Connection (T005)

From your local machine, test the SSH connection using the new key:

```bash
ssh -i ~/.ssh/hostaway-deploy root@72.60.233.157

# If successful, you'll see the Hostinger shell prompt
# Test passed! Exit and proceed to next step
exit
```

**If connection fails**:
- Verify public key was added correctly: `cat ~/.ssh/authorized_keys` on Hostinger
- Check permissions: `ls -la ~/.ssh/authorized_keys` (should be 600)
- Verify private key path: `ls -la ~/.ssh/hostaway-deploy`

---

## Step 4-15: Configure GitHub Repository Secrets

Navigate to your GitHub repository secrets page:
```
https://github.com/[YOUR_ORG]/[YOUR_REPO]/settings/secrets/actions
```

Click **"New repository secret"** for each of the following:

### T006: SSH_PRIVATE_KEY

1. **Name**: `SSH_PRIVATE_KEY`
2. **Value**: Full contents of `~/.ssh/hostaway-deploy` file:
   ```bash
   cat ~/.ssh/hostaway-deploy
   ```
3. Copy the ENTIRE output including headers:
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtz
   [... full key content ...]
   -----END OPENSSH PRIVATE KEY-----
   ```

**⚠️ IMPORTANT**: Include the header and footer lines!

---

### T007-T009: SSH Connection Secrets

| Secret Name | Value | Source |
|-------------|-------|--------|
| **SSH_HOST** | `72.60.233.157` | Hostinger server IP |
| **SSH_USERNAME** | `root` | SSH username |
| **DEPLOY_PATH** | `/opt/hostaway-mcp` | Deployment directory |

---

### T010-T012: Supabase Secrets

Navigate to your Supabase project: `https://app.supabase.com/project/[PROJECT_ID]/settings/api`

| Secret Name | Value | Location in Supabase |
|-------------|-------|----------------------|
| **SUPABASE_URL** | `https://[project].supabase.co` | Project Settings → API → Project URL |
| **SUPABASE_SERVICE_KEY** | `eyJhbGciOiJIUzI1NiIsInR5cCI6...` | Project Settings → API → service_role (secret key) |
| **SUPABASE_ANON_KEY** | `eyJhbGciOiJIUzI1NiIsInR5cCI6...` | Project Settings → API → anon (public key) |

---

### T013-T014: Hostaway API Secrets

Navigate to Hostaway account settings to retrieve:

| Secret Name | Value | Source |
|-------------|-------|--------|
| **HOSTAWAY_ACCOUNT_ID** | `[numeric ID]` | Hostaway account settings |
| **HOSTAWAY_SECRET_KEY** | `[alphanumeric string]` | Hostaway API settings |

---

## Step 16: Verify All Secrets (T015)

After adding all 9 secrets, verify they appear in your GitHub repository secrets list:

```
Settings → Secrets and variables → Actions → Repository secrets
```

**Required Secrets** (9 total):
- ✅ SSH_PRIVATE_KEY
- ✅ SSH_HOST
- ✅ SSH_USERNAME
- ✅ DEPLOY_PATH
- ✅ SUPABASE_URL
- ✅ SUPABASE_SERVICE_KEY
- ✅ SUPABASE_ANON_KEY
- ✅ HOSTAWAY_ACCOUNT_ID
- ✅ HOSTAWAY_SECRET_KEY

**Each secret should show**:
- Green checkmark when saved
- "Updated X minutes/hours ago"
- Values are NEVER displayed (security feature)

---

## Verification Checklist

Before proceeding to Phase 3, verify:

- [ ] SSH key pair generated (`~/.ssh/hostaway-deploy` and `~/.ssh/hostaway-deploy.pub` exist)
- [ ] Public key added to Hostinger `/root/.ssh/authorized_keys`
- [ ] SSH connection test passed using new key
- [ ] All 9 GitHub Secrets configured in repository
- [ ] Each secret shows green checkmark in GitHub UI
- [ ] No secrets committed to git repository (check with `git log -S "BEGIN OPENSSH"`)

---

## Troubleshooting

### SSH Connection Refused
- Check Hostinger VPS is running: `ping 72.60.233.157`
- Verify SSH service is active on Hostinger: `systemctl status sshd` (via console)
- Confirm port 22 is open (standard SSH port)

### Secret Not Saving in GitHub
- Ensure you have repository admin access
- Try refreshing the page and adding again
- Verify value doesn't contain special characters that need escaping
- For multiline secrets (SSH key), paste entire content including headers

### SSH Key Permissions Error
- Private key: `chmod 600 ~/.ssh/hostaway-deploy`
- Public key: `chmod 644 ~/.ssh/hostaway-deploy.pub`
- .ssh directory: `chmod 700 ~/.ssh`

---

## Next Steps

Once all secrets are configured and verified:

1. Mark tasks T003-T015 as complete in `specs/007-so-we-need/tasks.md`
2. Proceed to **Phase 3**: Implement GitHub Actions workflow
3. The workflow will use these secrets automatically via `${{ secrets.NAME }}` syntax

---

## Security Reminders

- ✅ Never commit private key to repository
- ✅ Never echo or print secret values in scripts
- ✅ GitHub automatically masks secret values in logs as `***`
- ✅ Rotate SSH keys every 90 days (calendar reminder recommended)
- ✅ Private key should remain on your local machine only
- ✅ GitHub encrypts secrets at rest using Libsodium

---

**Estimated Time**: 30-45 minutes for all manual steps

**Once complete, you'll have**: Secure authentication from GitHub Actions to Hostinger VPS with all necessary credentials configured.
