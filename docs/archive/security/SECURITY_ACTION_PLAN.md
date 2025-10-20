# Security Action Plan - Hostaway MCP

## Immediate Actions (Complete Within 4 Hours)

### 1. Rotate All Compromised Credentials

#### Supabase Service Keys
1. Log into [Supabase Dashboard](https://app.supabase.com)
2. Navigate to Settings → API
3. Regenerate both Anon and Service Role keys
4. Update all production deployments with new keys
5. Update local .env files with new keys

#### MCP API Keys
1. Access your MCP management interface
2. Revoke the exposed key: `mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk`
3. Generate new API keys
4. Update all systems using these keys

### 2. Secure Production Systems
```bash
# On production server
# 1. Update environment variables with new credentials
export SUPABASE_SERVICE_KEY="new-key-here"
export MCP_API_KEY="new-key-here"

# 2. Restart services to load new credentials
systemctl restart hostaway-mcp

# 3. Verify services are running with new credentials
curl http://localhost:8000/health
```

### 3. Remove Secrets from Repository
```bash
# Remove sensitive files from current working tree
git rm --cached ROOT_DEPLOY_COMMANDS.sh
git rm --cached QUICK_DEPLOY.sh
git rm --cached HOSTINGER_FILE_MANAGER_DEPLOY.md

# Create cleaned versions without secrets
cp deploy-clean.sh ROOT_DEPLOY_COMMANDS.sh
# Edit to add deployment logic without hardcoded secrets

# Commit the changes
git add .
git commit -m "security: remove hardcoded secrets from deployment scripts"
```

## Short-term Actions (Complete Within 48 Hours)

### 1. Clean Git History
```bash
# Install BFG Repo-Cleaner
brew install bfg

# Create a backup of your repository
cp -r hostaway-mcp hostaway-mcp-backup

# Remove secrets from history
bfg --replace-text passwords.txt hostaway-mcp
cd hostaway-mcp
git reflog expire --expire=now --all && git gc --prune=now --aggressive

# Force push cleaned history (coordinate with team)
git push --force
```

Create `passwords.txt` with patterns to remove:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9==>REMOVED_JWT_TOKEN
mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk==>REMOVED_API_KEY
```

### 2. Implement Pre-commit Hooks
Add to `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.28.0
    hooks:
      - id: gitleaks

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: detect-private-key
      - id: check-added-large-files
```

Install hooks:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### 3. Update Documentation
Replace all example credentials with clear placeholders:
- Change `mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk` to `<YOUR_MCP_API_KEY>`
- Change JWT examples to `<YOUR_SUPABASE_SERVICE_KEY>`
- Add security warnings to all documentation

## Medium-term Actions (Complete Within 1 Week)

### 1. Implement Secret Management

#### Option A: Environment-based (Simple)
```python
# src/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Required secrets
    supabase_url: str
    supabase_service_key: str
    mcp_api_key: str

    # Optional configurations
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("supabase_service_key", "mcp_api_key")
    def validate_not_placeholder(cls, v):
        if "YOUR_" in v or "placeholder" in v.lower():
            raise ValueError("Placeholder value detected in production configuration")
        return v

settings = Settings()
```

#### Option B: AWS Secrets Manager
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
secrets = get_secret("hostaway-mcp/production")
supabase_key = secrets['SUPABASE_SERVICE_KEY']
```

### 2. Set Up CI/CD Security Scanning

Add to GitHub Actions:
```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 3. Implement Monitoring and Alerting

```python
# src/middleware/security_monitor.py
import logging
from datetime import datetime
import hashlib

class SecurityMonitor:
    def __init__(self):
        self.logger = logging.getLogger("security")

    async def log_api_access(self, request, api_key_hash):
        """Log API key usage for audit trail"""
        self.logger.info({
            "timestamp": datetime.utcnow().isoformat(),
            "api_key_hash": api_key_hash,
            "endpoint": request.url.path,
            "method": request.method,
            "ip": request.client.host
        })

    async def detect_anomalies(self, api_key, request):
        """Detect suspicious activity"""
        # Check for unusual patterns
        if self.is_suspicious_pattern(request):
            await self.alert_security_team(api_key, request)
```

## Long-term Security Improvements

### 1. Security Training Program
- [ ] Conduct security awareness training for all developers
- [ ] Create secure coding guidelines specific to the project
- [ ] Regular security review sessions

### 2. Automated Security Testing
- [ ] Implement SAST (Static Application Security Testing)
- [ ] Set up DAST (Dynamic Application Security Testing)
- [ ] Regular penetration testing (quarterly)

### 3. Zero-Trust Architecture
- [ ] Implement mutual TLS for service communication
- [ ] Use short-lived tokens with automatic rotation
- [ ] Principle of least privilege for all service accounts

## Verification Checklist

After completing remediation:

- [ ] All production credentials have been rotated
- [ ] No secrets exist in current codebase
- [ ] Pre-commit hooks prevent secret commits
- [ ] CI/CD includes secret scanning
- [ ] Documentation uses only placeholder values
- [ ] Team has been notified of security practices
- [ ] Monitoring is in place for suspicious activity
- [ ] Incident response plan is documented

## Contact Information

**Security Team Lead:** [Your Name]
**Emergency Contact:** [Phone/Email]
**Escalation Path:** Security Team → CTO → CEO

## Additional Resources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Supabase Security Best Practices](https://supabase.com/docs/guides/platform/security)

---

**Last Updated:** October 15, 2025
**Next Review:** October 22, 2025
