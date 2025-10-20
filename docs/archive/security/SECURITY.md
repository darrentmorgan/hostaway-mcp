# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in the Hostaway MCP project, please report it responsibly:

1. **DO NOT** create a public GitHub issue
2. Email security details to: security@yourcompany.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We aim to respond within 48 hours and will work with you to understand and address the issue.

## Security Measures

### 1. Automated Security Scanning

Our codebase is protected by multiple layers of automated security scanning:

- **Pre-commit hooks**: Run on every commit
- **CI/CD pipeline**: Run on every push and pull request
- **Dependency scanning**: Daily automated checks
- **Secret detection**: Real-time scanning for credentials

### 2. Security Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Gitleaks** | Secret detection | `.gitleaks.toml` |
| **Bandit** | Python security audit | Pre-commit config |
| **Safety** | Dependency vulnerabilities | Pre-commit config |
| **Semgrep** | Static analysis | Auto-configured |
| **ESLint Security** | JavaScript/TypeScript | `.eslintrc.security.json` |

### 3. Run Security Audit

```bash
# Run comprehensive security audit
./scripts/security-audit.sh

# Run pre-commit security checks
pre-commit run --all-files

# Check for secrets only
pre-commit run gitleaks --all-files

# Check Python security
pre-commit run bandit --all-files
```

## Security Best Practices

### API Security

1. **Authentication**: All API endpoints require valid JWT tokens
2. **Rate Limiting**: Implemented per-user and per-IP
3. **Input Validation**: Pydantic models validate all inputs
4. **CORS**: Configured for allowed origins only

### Database Security

1. **Row Level Security (RLS)**: Enabled on all tables
2. **Encrypted Credentials**: Using Supabase Vault
3. **Parameterized Queries**: No raw SQL concatenation
4. **Least Privilege**: Database roles with minimal permissions

### Application Security

1. **No Hardcoded Secrets**: All secrets in environment variables
2. **Secure Headers**: CSP, HSTS, X-Frame-Options configured
3. **XSS Protection**: React's built-in protection + sanitization
4. **CSRF Protection**: Token-based protection

### Infrastructure Security

1. **HTTPS Only**: TLS 1.2+ enforced
2. **Security Updates**: Automated via Dependabot
3. **Container Scanning**: Docker images scanned for vulnerabilities
4. **Access Control**: Role-based permissions

## Security Headers

The application implements the following security headers:

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'
Referrer-Policy: origin-when-cross-origin
```

## Dependency Management

- **Lock Files**: `requirements.txt` and `package-lock.json` for reproducible builds
- **Regular Updates**: Weekly dependency updates
- **Vulnerability Scanning**: Automated scanning with Safety and npm audit
- **License Compliance**: All dependencies reviewed for compatible licenses

## Data Protection

1. **Encryption at Rest**: Database encryption enabled
2. **Encryption in Transit**: TLS for all connections
3. **PII Handling**: Minimal PII collection, encrypted storage
4. **Data Retention**: Automatic cleanup of old data
5. **GDPR Compliance**: User data export and deletion capabilities

## Incident Response

### If a Security Breach Occurs:

1. **Immediate Actions**:
   - Isolate affected systems
   - Rotate all credentials
   - Review access logs

2. **Investigation**:
   - Determine scope of breach
   - Identify root cause
   - Document timeline

3. **Remediation**:
   - Patch vulnerabilities
   - Update security measures
   - Notify affected users (if required)

4. **Post-Incident**:
   - Conduct security review
   - Update documentation
   - Implement additional controls

## Security Checklist for Developers

Before committing code:

- [ ] No hardcoded secrets or credentials
- [ ] All user inputs are validated
- [ ] SQL queries use parameterized statements
- [ ] Error messages don't expose sensitive information
- [ ] Authentication checks on all protected endpoints
- [ ] Proper authorization for resource access
- [ ] Security headers configured
- [ ] Dependencies updated and scanned
- [ ] Pre-commit hooks passing
- [ ] Security tests passing

## Compliance

This project aims to comply with:

- **OWASP Top 10**: Coverage for common vulnerabilities
- **GDPR**: Data protection for EU users
- **CCPA**: Privacy rights for California residents
- **SOC 2 Type II**: Security controls and practices
- **PCI DSS**: If payment processing is added

## Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-15 | Initial security policy |

## Questions?

For security questions that don't involve reporting vulnerabilities:
- Open a GitHub discussion
- Tag with `security` label

For vulnerability reports:
- Email: security@yourcompany.com
- PGP Key: [Add if available]

---

**Remember**: Security is everyone's responsibility. When in doubt, ask!
