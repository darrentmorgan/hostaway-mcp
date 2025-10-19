# Quick Start: Automated CI/CD Pipeline Setup

**Feature**: Automated CI/CD Pipeline for Hostinger Deployment
**Branch**: `007-so-we-need`
**Phase**: 1 - Design & Contracts
**Date**: 2025-10-19

## Overview

This guide walks you through setting up automated deployments to Hostinger VPS using GitHub Actions. After setup, every PR merge to `main` automatically deploys to production within 10 minutes.

**Time to Complete**: 30-45 minutes

---

## Prerequisites

Before you begin, ensure you have:

- ✅ GitHub repository admin access
- ✅ Hostinger VPS SSH access (root user recommended)
- ✅ Supabase project credentials (URL, service key, anon key)
- ✅ Hostaway API credentials (account ID, secret key)
- ✅ Docker and docker-compose installed on Hostinger VPS
- ✅ Application repository cloned on Hostinger at `/opt/hostaway-mcp`

---

## Step 1: Generate SSH Key Pair

Generate a dedicated SSH key for GitHub Actions deployments:

```bash
# On your local machine or secure workstation
ssh-keygen -t ed25519 -C "github-actions-deployment" -f ~/.ssh/hostaway-deploy
```

**Expected Output**:
```
Generating public/private ed25519 key pair.
Enter passphrase (empty for no passphrase): [press Enter - no passphrase]
Enter same passphrase again: [press Enter]
Your identification has been saved in /Users/you/.ssh/hostaway-deploy
Your public key has been saved in /Users/you/.ssh/hostaway-deploy.pub
```

**Important**: Do NOT use a passphrase (GitHub Actions cannot handle interactive passphrases).

**Result**: Two files created:
- `hostaway-deploy` - Private key (add to GitHub Secrets)
- `hostaway-deploy.pub` - Public key (add to Hostinger server)

---

## Step 2: Add Public Key to Hostinger

Copy the public key to your Hostinger VPS:

```bash
# Display public key
cat ~/.ssh/hostaway-deploy.pub

# Copy output, then SSH to Hostinger
ssh root@72.60.233.157

# On Hostinger VPS
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add public key to authorized_keys
cat >> ~/.ssh/authorized_keys <<'EOF'
[paste your public key here]
EOF

# Secure permissions
chmod 600 ~/.ssh/authorized_keys

# Exit Hostinger
exit
```

**Test SSH Connection**:
```bash
# On your local machine
ssh -i ~/.ssh/hostaway-deploy root@72.60.233.157

# If successful, you should see Hostinger shell prompt
# Exit and proceed to next step
exit
```

---

## Step 3: Configure GitHub Secrets

Navigate to your GitHub repository settings:

```
https://github.com/[YOUR_ORG]/[YOUR_REPO]/settings/secrets/actions
```

Click **"New repository secret"** and add the following 9 secrets:

### SSH Authentication Secrets

| Secret Name | Value | How to Get It |
|-------------|-------|---------------|
| `SSH_PRIVATE_KEY` | Full contents of `~/.ssh/hostaway-deploy` file | `cat ~/.ssh/hostaway-deploy` |
| `SSH_HOST` | `72.60.233.157` | Hostinger server IP address |
| `SSH_USERNAME` | `root` | SSH username on Hostinger |
| `DEPLOY_PATH` | `/opt/hostaway-mcp` | Deployment directory on server |

**Important**: For `SSH_PRIVATE_KEY`, copy the ENTIRE file including header and footer:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
[... full key content ...]
-----END OPENSSH PRIVATE KEY-----
```

### Application Environment Secrets

| Secret Name | Value | How to Get It |
|-------------|-------|---------------|
| `SUPABASE_URL` | `https://[project].supabase.co` | Supabase project settings → API → Project URL |
| `SUPABASE_SERVICE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6...` | Supabase project settings → API → service_role key |
| `SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6...` | Supabase project settings → API → anon public key |
| `HOSTAWAY_ACCOUNT_ID` | `123456` | Hostaway account settings |
| `HOSTAWAY_SECRET_KEY` | `a1b2c3d4e5f6...` | Hostaway API settings |

**Verification**:
- All 9 secrets should appear in the secrets list
- Each secret shows a green checkmark when saved
- Secret values are never displayed (security feature)

---

## Step 4: Create GitHub Actions Workflow

Create the workflow file in your repository:

```bash
# On your local machine, in your repository
mkdir -p .github/workflows

# Copy the workflow from contracts directory
cp specs/007-so-we-need/contracts/deploy-production.yml .github/workflows/deploy-production.yml

# Or create manually - see contracts/deploy-production.yml for full content
```

**Workflow File Location**: `.github/workflows/deploy-production.yml`

**Commit and Push**:
```bash
git add .github/workflows/deploy-production.yml
git commit -m "feat: add automated deployment workflow

- GitHub Actions workflow for Hostinger VPS deployment
- Triggers on PR merge to main
- SSH-based deployment with rollback on failure
- Health check verification post-deployment

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin 007-so-we-need
```

---

## Step 5: Test Deployment

### Option A: Manual Trigger (Recommended for First Test)

1. Navigate to GitHub Actions tab in your repository
2. Click on "Deploy to Production" workflow
3. Click "Run workflow" button
4. Select branch: `main`
5. Click green "Run workflow" button

**Expected Outcome**:
- Workflow starts within 30 seconds
- All steps complete successfully (green checkmarks)
- Deployment finishes in 5-10 minutes
- Health check passes
- Production server updated

### Option B: Create Test PR

1. Create a test branch with a minor change:
   ```bash
   git checkout -b test-ci-cd-pipeline
   echo "# CI/CD Pipeline Active" >> README.md
   git add README.md
   git commit -m "test: verify CI/CD pipeline"
   git push origin test-ci-cd-pipeline
   ```

2. Open pull request on GitHub
3. Get PR approved and merge to `main`
4. Watch GitHub Actions tab - deployment should start automatically

---

## Step 6: Verify Deployment

### Check GitHub Actions Logs

1. Navigate to: `https://github.com/[ORG]/[REPO]/actions`
2. Click on the most recent "Deploy to Production" run
3. Verify all steps show green checkmarks
4. Expand "Deploy to Hostinger" step
5. Confirm you see:
   - Secret values masked as `***`
   - "Health check passed"
   - "Deployment successful"

### Check Production Server

```bash
# SSH to Hostinger
ssh root@72.60.233.157

# Check Docker containers
cd /opt/hostaway-mcp
docker compose -f docker-compose.prod.yml ps

# Expected output: Container running with "Up" status

# Check health endpoint
curl http://localhost:8080/health

# Expected output: {"status": "healthy", ...}

# Check deployment backups exist
ls -la backups/

# Expected output: Directories with timestamp format YYYYMMDD-HHMMSS
```

---

## Troubleshooting

### Deployment Fails: "Permission denied (publickey)"

**Cause**: SSH key not properly configured

**Solution**:
1. Verify public key is in `~/.ssh/authorized_keys` on Hostinger
2. Check file permissions: `chmod 600 ~/.ssh/authorized_keys`
3. Verify private key in GitHub Secrets includes header/footer
4. Test SSH connection manually: `ssh -i ~/.ssh/hostaway-deploy root@72.60.233.157`

### Deployment Fails: "Health check failed"

**Cause**: Application not starting properly

**Solution**:
1. SSH to Hostinger: `ssh root@72.60.233.157`
2. Check Docker logs: `docker compose -f docker-compose.prod.yml logs`
3. Verify `.env` file created with correct values: `cat .env`
4. Check container status: `docker compose -f docker-compose.prod.yml ps`
5. Manual health check: `curl -v http://localhost:8080/health`

### Deployment Fails: "Secret not found"

**Cause**: GitHub Secrets not configured

**Solution**:
1. Navigate to repository settings → Secrets and variables → Actions
2. Verify all 9 secrets are present
3. Re-add any missing secrets
4. Re-run workflow

### Deployment Timeout (>10 minutes)

**Cause**: Server under heavy load or network issues

**Solution**:
1. Check Hostinger server load: `ssh root@72.60.233.157 'uptime'`
2. Check Docker build cache: `docker system df`
3. Consider increasing timeout in workflow file (max 30 minutes)
4. Investigate network latency to Hostinger

---

## Daily Usage

### Deploying Changes

1. Create feature branch
2. Make code changes
3. Open pull request
4. Get PR approved
5. Merge PR to `main`
6. **Deployment happens automatically** - no manual steps!

### Monitoring Deployments

- GitHub Actions tab shows real-time deployment progress
- Email notifications sent on deployment failure
- Deployment logs available for 90 days
- Health check endpoint: `http://72.60.233.157:8080/health`

### Rollback on Failure

**Automatic Rollback**:
- If health check fails, deployment automatically rolls back
- Previous version restored from backup
- Workflow marked as failed with error details

**Manual Rollback** (if needed):
```bash
ssh root@72.60.233.157
cd /opt/hostaway-mcp/backups

# List backups
ls -lt

# Restore from specific backup
BACKUP_DIR="20251019-143022"  # Use actual timestamp
cd /opt/hostaway-mcp
docker compose -f docker-compose.prod.yml down
docker load < "backups/$BACKUP_DIR/image.tar"
docker compose -f docker-compose.prod.yml up -d
```

---

## Maintenance

### Rotate SSH Keys (Every 90 Days)

1. Generate new key pair: `ssh-keygen -t ed25519 -C "github-actions-deployment-$(date +%Y%m)" -f ~/.ssh/hostaway-deploy-new`
2. Add new public key to Hostinger: `cat ~/.ssh/hostaway-deploy-new.pub >> ~/.ssh/authorized_keys`
3. Update `SSH_PRIVATE_KEY` secret in GitHub with new private key
4. Test deployment
5. Remove old public key from Hostinger: `vim ~/.ssh/authorized_keys`

### Update Environment Variables

1. Update secret in GitHub repository settings
2. Trigger manual deployment or merge any PR to main
3. New .env file created on next deployment
4. No server SSH required

### Clean Up Old Backups

Automatic cleanup keeps last 5 backups. For manual cleanup:

```bash
ssh root@72.60.233.157
cd /opt/hostaway-mcp/backups
ls -t | tail -n +6 | xargs rm -rf
```

---

## Security Checklist

- [ ] SSH key generated without passphrase
- [ ] Private key never committed to repository
- [ ] All 9 GitHub Secrets configured
- [ ] Secret values masked in workflow logs (test by viewing a run)
- [ ] `.env` file has 600 permissions on server
- [ ] Only repository admins can modify secrets
- [ ] SSH key rotation scheduled (calendar reminder)
- [ ] Test deployment succeeded
- [ ] Health check endpoint returns 200 OK

---

## Success Criteria Validation

After setup, verify the following outcomes:

- ✅ **SC-001**: PR merged to main → changes live within 10 minutes
- ✅ **SC-003**: Workflow logs show `***` for all secret values
- ✅ **SC-004**: Deployment failures detected within 30 seconds (test with broken code)
- ✅ **SC-006**: Failed deployments preserve previous version (test rollback)
- ✅ **SC-007**: Can troubleshoot via GitHub Actions logs (no server access needed)
- ✅ **SC-008**: Manual deployment time reduced from 15 minutes to 0

---

## Next Steps

1. **Test Rollback**: Intentionally break a deployment to verify automatic rollback works
2. **Monitor Success Rate**: Track deployment success over first 20 deployments (target: 95%+)
3. **Schedule Key Rotation**: Add calendar reminder for 90 days from setup
4. **Document Runbook**: Add custom failure scenarios to team documentation

---

## Support

**Documentation**:
- Full specification: `specs/007-so-we-need/spec.md`
- Implementation plan: `specs/007-so-we-need/plan.md`
- Workflow contract: `specs/007-so-we-need/contracts/deploy-production.yml`

**GitHub Actions**:
- Workflow runs: `https://github.com/[ORG]/[REPO]/actions`
- Secrets management: `https://github.com/[ORG]/[REPO]/settings/secrets/actions`

**External References**:
- GitHub Actions documentation: https://docs.github.com/en/actions
- GitHub Secrets security: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- SSH key best practices: https://goteleport.com/blog/comparing-ssh-keys/
