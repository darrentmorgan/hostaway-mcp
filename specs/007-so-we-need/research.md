# Research: CI/CD Pipeline Implementation

**Feature**: Automated CI/CD Pipeline for Hostinger Deployment
**Phase**: 0 - Research & Decision Documentation
**Date**: 2025-10-19

## Overview

This document consolidates research findings for implementing automated CI/CD deployment to Hostinger VPS using GitHub Actions, addressing all technical unknowns identified during planning.

## Research Areas

### 1. GitHub Actions for SSH-Based Deployments

**Decision**: Use GitHub Actions with `appleboy/ssh-action` for secure SSH deployment

**Rationale**:
- Official GitHub Actions runners have SSH client pre-installed
- `appleboy/ssh-action` is well-maintained (200k+ usage, active development)
- Supports key-based authentication with secrets
- Automatic secret masking in logs
- Simple YAML configuration for SSH commands

**Alternatives Considered**:
- **Direct SSH via bash**: More manual setup, harder secret management
- **Custom Docker container with SSH**: Unnecessary complexity for simple deployment
- **Third-party deployment services** (DeployHQ, Buddy): Additional cost, vendor lock-in

**Implementation Pattern**:
```yaml
- name: Deploy to Hostinger
  uses: appleboy/ssh-action@v1.0.0
  with:
    host: ${{ secrets.HOST }}
    username: ${{ secrets.USERNAME }}
    key: ${{ secrets.SSH_PRIVATE_KEY }}
    script: |
      cd /opt/hostaway-mcp
      ./deploy-script.sh
```

**References**:
- GitHub Actions documentation: https://docs.github.com/en/actions
- appleboy/ssh-action: https://github.com/appleboy/ssh-action
- GitHub Secrets: https://docs.github.com/en/actions/security-guides/encrypted-secrets

---

### 2. Secret Management Strategy

**Decision**: Use GitHub Actions Secrets for all sensitive data with environment-specific organization

**Secret Structure**:
```
Repository Secrets (for production deployment):
- SSH_PRIVATE_KEY: RSA private key for Hostinger authentication
- SSH_HOST: Hostinger server IP (72.60.233.157)
- SSH_USERNAME: Server username (root)
- DEPLOY_PATH: Deployment directory (/opt/hostaway-mcp)

Environment Variables (passed to server):
- SUPABASE_URL
- SUPABASE_SERVICE_KEY
- SUPABASE_ANON_KEY
- HOSTAWAY_ACCOUNT_ID
- HOSTAWAY_SECRET_KEY
```

**Rationale**:
- GitHub encrypts secrets at rest using Libsodium
- Secrets are automatically masked in workflow logs
- Secrets can only be accessed by workflows in the same repository
- No additional secret management service needed

**Alternatives Considered**:
- **HashiCorp Vault**: Over-engineered for single deployment target
- **AWS Secrets Manager**: Requires AWS account, additional cost
- **Environment files in repository**: SECURITY RISK - rejected

**Security Best Practices**:
- Never echo or print secret values directly
- Use `${{ secrets.NAME }}` syntax (auto-masked)
- Rotate SSH keys every 90 days
- Audit secret access via GitHub Actions logs

**References**:
- GitHub Secrets encryption: https://docs.github.com/en/actions/security-guides/encrypted-secrets#about-encrypted-secrets
- Secret masking: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#masking-a-value-in-log

---

### 3. Deployment Rollback Strategy

**Decision**: Implement backup-before-deploy pattern with automatic rollback on failure

**Implementation Approach**:

**Phase 1 - Backup Creation**:
```bash
# Create timestamped backup of current deployment
BACKUP_DIR="/opt/hostaway-mcp/backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r /opt/hostaway-mcp/src "$BACKUP_DIR/"
cp /opt/hostaway-mcp/.env "$BACKUP_DIR/"
docker save hostaway-mcp:latest > "$BACKUP_DIR/image.tar"
```

**Phase 2 - Deploy with Health Check**:
```bash
# Deploy new version
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

# Wait for container startup
sleep 10

# Health check
if ! curl -f http://localhost:8080/health; then
  echo "Health check failed - rolling back"
  docker compose -f docker-compose.prod.yml down
  docker load < "$BACKUP_DIR/image.tar"
  docker compose -f docker-compose.prod.yml up -d
  exit 1
fi
```

**Phase 3 - Cleanup Old Backups**:
```bash
# Keep only last 5 backups
cd /opt/hostaway-mcp/backups
ls -t | tail -n +6 | xargs rm -rf
```

**Rationale**:
- Simple file-based backup (no database migrations to worry about)
- Health check provides quick failure detection
- Automatic rollback prevents manual intervention
- Backup retention prevents disk space issues

**Alternatives Considered**:
- **Git-based rollback**: Requires re-deploy from previous commit (slower)
- **Blue-green deployment**: Requires 2x resources on single VPS (not feasible)
- **Container snapshots**: Docker doesn't support atomic rollback natively

**References**:
- Docker save/load: https://docs.docker.com/engine/reference/commandline/save/
- Health checks: https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck

---

### 4. Concurrent Deployment Prevention

**Decision**: Use GitHub Actions concurrency control with cancel-in-progress

**Implementation**:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

concurrency:
  group: production-deployment
  cancel-in-progress: false  # Wait for current deployment to finish
```

**Rationale**:
- GitHub Actions built-in concurrency control
- `cancel-in-progress: false` ensures deployment completes before starting next
- Prevents race conditions from concurrent merges
- Queues deployments instead of failing

**Alternatives Considered**:
- **Manual deployment locking**: Requires external service (Redis, DynamoDB)
- **Deployment queue service**: Additional infrastructure complexity
- **Fail on concurrent runs**: Would block legitimate deployments

**Edge Case Handling**:
- If deployment hangs, GitHub Actions timeout (30 min default) will cancel
- Subsequent deployments will start after timeout
- Failed deployments trigger notifications for manual investigation

**References**:
- GitHub Actions concurrency: https://docs.github.com/en/actions/using-jobs/using-concurrency

---

### 5. Environment Variable Transfer

**Decision**: Generate `.env` file on deployment server from GitHub Secrets

**Implementation Pattern**:
```yaml
- name: Deploy with Environment Variables
  uses: appleboy/ssh-action@v1.0.0
  with:
    host: ${{ secrets.SSH_HOST }}
    username: ${{ secrets.SSH_USERNAME }}
    key: ${{ secrets.SSH_PRIVATE_KEY }}
    script: |
      cd /opt/hostaway-mcp

      # Create .env from secrets (values masked in logs)
      cat > .env <<EOF
      SUPABASE_URL=${{ secrets.SUPABASE_URL }}
      SUPABASE_SERVICE_KEY=${{ secrets.SUPABASE_SERVICE_KEY }}
      SUPABASE_ANON_KEY=${{ secrets.SUPABASE_ANON_KEY }}
      HOSTAWAY_ACCOUNT_ID=${{ secrets.HOSTAWAY_ACCOUNT_ID }}
      HOSTAWAY_SECRET_KEY=${{ secrets.HOSTAWAY_SECRET_KEY }}
      ENVIRONMENT=production
      EOF

      # Secure permissions
      chmod 600 .env

      # Deploy
      ./deploy-to-hostinger-secure.sh
```

**Rationale**:
- Secrets automatically masked in GitHub Actions logs
- `.env` file never committed to repository
- File permissions (600) prevent unauthorized reading
- Deployment script expects `.env` to exist

**Alternatives Considered**:
- **SCP transfer**: More complex, same security outcome
- **Docker secrets**: Requires Docker Swarm (not using orchestration)
- **Environment variables in docker-compose**: Harder to manage 10+ variables

**Security Considerations**:
- `.env` file created during deployment only
- File permissions restrict access to root user
- File deleted on failed deployments (rollback cleans up)

**References**:
- Docker Compose env files: https://docs.docker.com/compose/environment-variables/

---

### 6. Deployment Timing and Performance

**Decision**: Optimize for <5 minute total deployment time

**Timing Breakdown**:
1. **Workflow trigger**: <30 seconds (GitHub Actions startup)
2. **Code transfer**: <1 minute (tar.gz over SSH, ~50MB)
3. **Docker build**: 2-3 minutes (cached layers, only changed files rebuild)
4. **Container restart**: <30 seconds (graceful shutdown + startup)
5. **Health check**: <10 seconds (HTTP GET to /health endpoint)

**Total**: ~4-5 minutes (well under 10 minute requirement)

**Optimizations**:
- Use `--no-cache` only when dependency changes detected
- Implement Docker layer caching for Python dependencies
- Use `docker compose build --pull=false` to avoid re-pulling base images
- Parallel steps where possible (not many in sequential deployment)

**Performance Monitoring**:
- GitHub Actions shows step-by-step timing
- Add `time` command to bash scripts for granular measurements
- Track deployment duration as Success Criteria metric

**References**:
- Docker build optimization: https://docs.docker.com/build/cache/

---

### 7. Failure Notification Strategy

**Decision**: Use GitHub Actions built-in notifications + workflow status badges

**Notification Channels**:
1. **GitHub UI**: Workflow run status visible in Actions tab
2. **Email**: GitHub sends email on workflow failure (user preference)
3. **GitHub Mobile App**: Push notifications for workflow events
4. **Status Badge**: Add to README.md for visibility

**Status Badge Implementation**:
```markdown
[![Deploy to Production](https://github.com/USER/REPO/actions/workflows/deploy-production.yml/badge.svg)](https://github.com/USER/REPO/actions/workflows/deploy-production.yml)
```

**Failure Details Available**:
- Full deployment logs in GitHub Actions UI
- Error messages from failed steps
- Health check response (if available)
- Rollback status

**Rationale**:
- No additional services required (Slack, PagerDuty)
- GitHub provides comprehensive notification system
- Developers already monitor GitHub for PR activity

**Alternatives Considered**:
- **Slack webhook**: Additional configuration, not needed for small team
- **Email-only**: GitHub already provides this
- **PagerDuty**: Over-engineered for non-critical deployments

**References**:
- GitHub Actions notifications: https://docs.github.com/en/account-and-profile/managing-subscriptions-and-notifications-on-github/setting-up-notifications/configuring-notifications
- Workflow status badges: https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/adding-a-workflow-status-badge

---

### 8. SSH Key Generation and Setup

**Decision**: Use Ed25519 SSH keys for authentication (modern, secure)

**Key Generation Process**:
```bash
# On local machine or secure workstation
ssh-keygen -t ed25519 -C "github-actions-deployment" -f ~/.ssh/hostaway-deploy

# Output:
# - Private key: hostaway-deploy (add to GitHub Secrets)
# - Public key: hostaway-deploy.pub (add to Hostinger server)
```

**Server Setup**:
```bash
# On Hostinger VPS (as root)
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys <<EOF
[paste public key here]
EOF
chmod 600 ~/.ssh/authorized_keys
```

**GitHub Secret Configuration**:
```
Name: SSH_PRIVATE_KEY
Value: [entire contents of hostaway-deploy private key file]
```

**Rationale**:
- Ed25519 is faster and more secure than RSA
- Smaller key size (256-bit vs 2048-bit RSA)
- GitHub Actions supports Ed25519 natively
- Industry standard for modern SSH deployments

**Alternatives Considered**:
- **RSA 4096**: Larger, slower, but widely compatible (not needed)
- **ECDSA**: Less common, no significant advantage over Ed25519

**Security Best Practices**:
- Generate unique key for deployments (don't reuse personal keys)
- Never commit private key to repository
- Rotate key every 90 days
- Restrict key to deployment user only (no shared keys)

**References**:
- SSH key types comparison: https://goteleport.com/blog/comparing-ssh-keys/
- GitHub Actions SSH auth: https://github.com/appleboy/ssh-action#key-based-authentication

---

## Summary of Decisions

| Decision Area | Technology/Approach | Justification |
|---------------|---------------------|---------------|
| CI/CD Platform | GitHub Actions | Native integration, no additional cost |
| SSH Deployment | appleboy/ssh-action | Well-maintained, 200k+ usage |
| Secret Management | GitHub Secrets | Built-in, encrypted, auto-masked |
| Rollback Strategy | Backup-before-deploy + health check | Simple, reliable, fast recovery |
| Concurrency Control | GitHub Actions concurrency groups | Built-in, prevents race conditions |
| Environment Variables | Generated .env file | Secure transfer, Docker Compose compatible |
| Notifications | GitHub Actions notifications | Native, sufficient for team size |
| SSH Keys | Ed25519 | Modern, secure, performant |

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| GitHub Actions outage | Deployments blocked | Manual deployment script available as backup |
| SSH key compromise | Unauthorized access | Key rotation every 90 days, audit access logs |
| Failed deployment with bad rollback | Downtime | Test rollback process in non-production |
| Disk space issues on Hostinger | Build failures | Backup cleanup, monitor disk usage |
| Concurrent merge race conditions | Deployment conflicts | Concurrency control with queue |

## Next Steps

With all research complete, proceed to:
- **Phase 1**: Generate data-model.md (minimal - workflow configuration schema)
- **Phase 1**: Generate contracts (GitHub Actions workflow YAML structure)
- **Phase 1**: Generate quickstart.md (setup guide for developers)
