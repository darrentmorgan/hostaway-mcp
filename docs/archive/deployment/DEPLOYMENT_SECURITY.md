# Deployment Security Guidelines

**Last Updated**: October 15, 2025

## ✅ Security Measures Implemented

### 1. Sensitive Files in .gitignore

The following files are **NEVER** committed to git:

```gitignore
# Credentials and secrets
.env
.env.local
*.env
secrets-to-replace.txt

# Deployment scripts with credentials
deploy_with_password.exp
deploy-to-hostinger.sh
clean-git-history.sh
```

### 2. Template-Based Deployment

**Instead of hardcoded credentials**, we use template files:

- `deploy_with_password.exp.template` - Template with placeholders
- `deploy-to-hostinger-secure.sh` - Secure deployment without credentials

**Setup Process**:
```bash
# 1. Copy template
cp deploy_with_password.exp.template deploy_with_password.exp

# 2. Edit with your credentials
nano deploy_with_password.exp

# 3. Set restrictive permissions
chmod 700 deploy_with_password.exp

# 4. Deploy
./deploy_with_password.exp
```

### 3. Git History Cleaned

- ✅ All secrets removed from git history using BFG Repo-Cleaner
- ✅ 118 secrets sanitized
- ✅ Force-pushed cleaned history to remote
- ✅ Verified: 0 secrets remaining (gitleaks scan)

### 4. Pre-commit Hooks

**Automatic secret detection** before every commit:
- Gitleaks - Secret scanner
- Bandit - Python security
- Safety - Dependency vulnerabilities
- Semgrep - Static analysis
- ESLint Security - JS/TS security

## ⚠️ Important Security Rules

### DO:
- ✅ Use environment variables for all credentials
- ✅ Keep `.env` files local (never commit)
- ✅ Use template files with placeholders
- ✅ Set restrictive file permissions (600/700)
- ✅ Rotate credentials after exposure
- ✅ Use pre-commit hooks

### DON'T:
- ❌ Hardcode passwords in scripts
- ❌ Commit credentials to git
- ❌ Share .env files via email/slack
- ❌ Include credentials in documentation
- ❌ Skip pre-commit hooks (--no-verify)
- ❌ Reuse passwords across environments

## 🔐 Current Deployment Credentials

**Server**: 72.60.233.157
**User**: root
**Authentication**: SSH password (rotate regularly!)

### Credential Locations

**Production**:
- Server `.env` file: `/opt/hostaway-mcp/.env`
- Local template: `.env.example`

**Development**:
- Local `.env` file (NOT in git)
- Use `.env.example` as reference

## 🚀 Deployment Workflow

### Secure Deployment Steps

1. **Prepare Locally**
   ```bash
   # Run tests
   pytest tests/ -v

   # Check for secrets
   gitleaks detect --config .gitleaks.toml
   ```

2. **Deploy Using Template**
   ```bash
   # Copy template (first time only)
   cp deploy_with_password.exp.template deploy_with_password.exp

   # Edit with YOUR credentials
   nano deploy_with_password.exp

   # Run deployment
   ./deploy_with_password.exp
   ```

3. **Verify Deployment**
   ```bash
   # Check server health
   curl http://72.60.233.157:8080/health

   # View logs
   ssh root@72.60.233.157 'tail -f /tmp/mcp-server.log'
   ```

## 📋 Post-Deployment Checklist

After every deployment:

- [ ] Verify health endpoint responding
- [ ] Check server logs for errors
- [ ] Test API endpoints
- [ ] Verify environment variables loaded
- [ ] Confirm no credentials in logs
- [ ] Update deployment documentation

## 🔄 Credential Rotation Schedule

**Regular Rotation**:
- SSH passwords: Every 90 days
- API keys: Every 90 days
- Service keys: Every 180 days

**Immediate Rotation Required If**:
- Credentials exposed in git
- Suspected unauthorized access
- Team member departure
- Security incident

See `KEY_ROTATION_PLAN.md` for detailed procedures.

## 📞 Security Contacts

**Security Issues**: Report immediately
**Credential Exposure**: Follow `KEY_ROTATION_PLAN.md`
**Deployment Problems**: Check logs first

---

**Remember**: Security is everyone's responsibility. When in doubt, ask!
