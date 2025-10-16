# Rollback Procedure
# Context Window Protection - Cursor-Based Pagination

**Version**: 1.0
**Date**: October 15, 2025
**Feature**: 005-project-brownfield-hardening

## Overview

This document provides step-by-step procedures for rolling back the cursor-based pagination feature in case of critical issues in production.

## When to Rollback

### Critical (Immediate Rollback)

Execute rollback immediately if ANY of these conditions occur:

- [ ] **Data Corruption**: Database records corrupted or data loss detected
- [ ] **Security Breach**: Authentication bypass or data exposure discovered
- [ ] **Complete Service Failure**: API completely unavailable for >5 minutes
- [ ] **Error Rate >10%**: More than 10% of requests failing
- [ ] **P0 Incident**: Critical business impact affecting multiple customers

### High Priority (Rollback within 1 hour)

- [ ] **Error Rate 5-10%**: Sustained high error rate
- [ ] **Performance Degradation >3x**: Response times 3x slower than baseline
- [ ] **Memory Leak**: OOM errors occurring frequently
- [ ] **Customer Escalations**: Multiple high-priority support tickets
- [ ] **Monitoring Failure**: Unable to observe system health

### Medium Priority (Consider Rollback)

- [ ] **Error Rate 1-5%**: Elevated but manageable error rate
- [ ] **Performance Degradation 2-3x**: Slower but functional
- [ ] **Feature Broken**: Pagination not working but system operational
- [ ] **Low Adoption**: <5% pagination adoption after 24 hours

## Rollback Decision Matrix

| Condition | Error Rate | Performance | Decision |
|-----------|-----------|-------------|----------|
| Normal | <1% | p95 <500ms | ✅ No action |
| Warning | 1-5% | p95 500-1000ms | ⚠️ Monitor closely |
| Alert | 5-10% | p95 1-2s | 🔶 Prepare rollback |
| Critical | >10% | p95 >2s | 🔴 Execute rollback |

## Pre-Rollback Checklist

Before initiating rollback:

- [ ] **Confirm Issue**: Verify the issue is caused by the pagination feature
- [ ] **Notify Team**: Alert #oncall and #engineering in Slack
- [ ] **Create Incident**: Open incident ticket with severity level
- [ ] **Document State**: Capture current metrics, logs, and error examples
- [ ] **Backup Current**: Tag current deployment in git
- [ ] **Identify Previous Version**: Confirm stable version to roll back to
- [ ] **Communication**: Notify stakeholders of impending rollback

### Pre-Rollback Communication Template

**Slack (#oncall):**
```
🚨 ROLLBACK INITIATED
Feature: Cursor-based Pagination
Reason: [Brief description]
Severity: P0/P1/P2
Lead: @engineer-name
Status page: [link]
Incident ticket: [link]
ETA: 10 minutes
```

**Status Page:**
```
We are currently investigating elevated error rates on the API.
We are rolling back a recent feature deployment to restore service.
No data has been lost.
ETA to resolution: 10 minutes
```

## Rollback Procedures

### Procedure 1: Application-Only Rollback

Use when: Pagination feature has issues but no database changes

**Time Estimate**: 5-10 minutes

#### Step 1: Enable Maintenance Mode (30 seconds)

```bash
# Update status file
echo "maintenance" > /var/www/maintenance_status

# Or update load balancer health check
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:region:account:targetgroup/name \
  --health-check-path /maintenance
```

- [ ] Maintenance mode enabled
- [ ] Verify traffic stopped
- [ ] Post update on status page

#### Step 2: Identify Stable Version (1 minute)

```bash
# List recent tags
git tag --sort=-creatordate | head -5

# Example output:
# v0.1.0-pagination  <-- Current (failing)
# v0.1.0-rc1         <-- Candidate
# v0.0.9             <-- Stable (pre-pagination)
```

- [ ] Stable version identified: `__________`
- [ ] Version verified in changelog

#### Step 3: Revert Application Code (2 minutes)

```bash
# Checkout previous stable version
git fetch --all --tags
git checkout tags/v0.0.9 -b rollback-$(date +%Y%m%d-%H%M%S)

# Verify you're on the right version
git log --oneline -5

# Install dependencies (matching that version)
uv sync
```

- [ ] Code reverted to stable version
- [ ] Dependencies installed
- [ ] No compilation errors

#### Step 4: Restart Application (1 minute)

```bash
# Using systemd
sudo systemctl restart hostaway-mcp

# OR using Docker
docker-compose restart api

# OR using supervisord
supervisorctl restart hostaway-mcp

# Wait for startup
sleep 5
```

- [ ] Application restarted
- [ ] Process running (check with `ps aux | grep hostaway`)
- [ ] No startup errors in logs

#### Step 5: Verify Rollback (2 minutes)

```bash
# Health check
curl http://localhost:8000/health
# Should return HTTP 200

# Test old pagination format (should work)
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/api/listings?limit=10"
# Should return items array

# Check logs for errors
tail -f /var/log/hostaway-mcp/application.log
# Should show successful requests
```

- [ ] Health endpoint returns 200
- [ ] API requests succeed
- [ ] No errors in logs
- [ ] Response time normal (<500ms)

#### Step 6: Disable Maintenance Mode (30 seconds)

```bash
# Remove maintenance status
rm /var/www/maintenance_status

# OR restore load balancer
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:region:account:targetgroup/name \
  --health-check-path /health
```

- [ ] Maintenance mode disabled
- [ ] Traffic flowing to application
- [ ] No immediate errors

#### Step 7: Monitor (5-10 minutes)

Watch key metrics for 10 minutes:

```bash
# Monitor error rate
watch -n 10 'curl -s http://localhost:8000/health | jq .context_protection.oversized_events'

# Monitor logs
tail -f /var/log/hostaway-mcp/application.log | grep -i error
```

- [ ] Error rate <1%
- [ ] Response time p95 <500ms
- [ ] Memory usage stable
- [ ] No customer complaints

### Procedure 2: Full Rollback (with Database)

Use when: Database migrations need to be reverted

**Time Estimate**: 15-20 minutes

#### Prerequisites

- [ ] Database backup exists and verified
- [ ] Database backup is recent (<24 hours)
- [ ] Backup restoration tested in staging

#### Step 1-2: Same as Procedure 1

Follow Steps 1-2 from Procedure 1 (maintenance mode + identify version)

#### Step 3: Database Backup (2 minutes)

```bash
# Create safety backup before rollback
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  > backup_pre_rollback_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_pre_rollback_*.sql
```

- [ ] Safety backup created
- [ ] Backup file size reasonable (>1KB)
- [ ] Backup uploaded to S3/secure storage

#### Step 4: Revert Database Migrations (3 minutes)

```bash
# Check current migration version
alembic current

# Revert to pre-pagination migration
alembic downgrade -1

# OR specify exact version
alembic downgrade <migration-id>

# Verify migration reverted
alembic current
```

- [ ] Migration reverted successfully
- [ ] Database schema verified
- [ ] No migration errors in logs

**Alternative: Restore from Backup (if downgrade fails)**

```bash
# Stop application first
sudo systemctl stop hostaway-mcp

# Restore database
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < backup_stable.sql

# Restart application
sudo systemctl start hostaway-mcp
```

#### Step 5-7: Same as Procedure 1

Follow Steps 4-7 from Procedure 1 (restart, verify, disable maintenance, monitor)

### Procedure 3: Partial Rollback (Feature Flag)

Use when: Want to disable pagination without full rollback

**Time Estimate**: 2-5 minutes

#### Step 1: Disable Pagination via Configuration (1 minute)

```bash
# Update config file
cat > config.yaml <<EOF
context_protection:
  pagination_enabled: false  # Disable pagination
  output_token_threshold: 10000  # Increase threshold
EOF

# Reload configuration (hot-reload)
kill -HUP $(pgrep -f "python.*hostaway-mcp")
```

- [ ] Configuration updated
- [ ] Application reloaded config (check logs for "Config reloaded")
- [ ] No restart required

#### Step 2: Verify Feature Disabled (1 minute)

```bash
# Test endpoint
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/api/listings?limit=10"

# Should return old format (without pagination)
# Response should have "listings" field instead of "items"
```

- [ ] Pagination disabled
- [ ] Old format returned
- [ ] No errors

This approach keeps the new code deployed but disables the feature.

## Post-Rollback Actions

### Immediate (Within 1 hour)

- [ ] **Update Status Page**: "Service restored. Investigating root cause."
- [ ] **Notify Customers**: Email to affected users (if any)
- [ ] **Update Incident Ticket**: Mark as resolved with rollback details
- [ ] **Team Notification**: Post update in Slack

```slack
✅ ROLLBACK COMPLETE
Feature: Cursor-based Pagination
Status: Rolled back successfully
Service: Fully operational
Error rate: 0.2% (normal)
Next steps: Root cause analysis
Incident ticket: [link]
```

### Within 24 Hours

- [ ] **Root Cause Analysis**: Document what went wrong
- [ ] **Metrics Review**: Analyze metrics leading up to failure
- [ ] **Log Analysis**: Review error logs for patterns
- [ ] **Code Review**: Identify problematic code
- [ ] **Fix Development**: Create hotfix branch
- [ ] **Testing**: Comprehensive testing of fix

### Within 1 Week

- [ ] **Post-Mortem Meeting**: Team discussion of incident
- [ ] **Documentation Update**: Update deployment checklist based on learnings
- [ ] **Process Improvements**: Identify gaps in testing/monitoring
- [ ] **Redeploy Plan**: Schedule re-deployment of fixed feature

## Root Cause Analysis Template

```markdown
# Incident Post-Mortem: Pagination Rollback

## Summary
[Brief description of what happened]

## Timeline
- 14:00 UTC: Deployment began
- 14:15 UTC: Error rate spike detected
- 14:20 UTC: Alert triggered
- 14:25 UTC: Rollback initiated
- 14:35 UTC: Service restored

## Root Cause
[Technical explanation of what caused the issue]

## Impact
- Duration: X minutes
- Affected users: Y customers
- Error rate: Z%
- Revenue impact: $X (if applicable)

## What Went Well
- Fast detection (5 minutes)
- Smooth rollback (10 minutes)
- Clear communication

## What Didn't Go Well
- Issue not caught in staging
- Alert threshold too high
- Documentation incomplete

## Action Items
1. [ ] Add test case for [scenario]
2. [ ] Lower alert threshold from X to Y
3. [ ] Update deployment checklist
4. [ ] Improve staging environment

## Lessons Learned
[Key takeaways for the team]
```

## Rollback Testing

Test rollback procedure in staging **before** production deployment:

### Staging Rollback Test

```bash
# 1. Deploy pagination feature to staging
git checkout 005-project-brownfield-hardening
# ... deploy ...

# 2. Simulate failure
# (inject errors, overload system, etc.)

# 3. Execute rollback procedure
# ... follow Procedure 1 ...

# 4. Verify rollback worked
# ... test endpoints ...

# 5. Document time taken
# Expected: <10 minutes
# Actual: _____ minutes

# 6. Identify any issues with rollback process
```

### Rollback Drill Schedule

- **Pre-Deployment**: Test rollback in staging
- **Post-Deployment**: Quarterly rollback drills
- **After Incident**: Test updated rollback procedure

## Emergency Contacts

| Role | Primary | Secondary | Escalation |
|------|---------|-----------|------------|
| On-Call Engineer | [Name] | [Name] | DevOps Lead |
| DevOps Lead | [Name] | [Name] | Engineering Manager |
| Engineering Manager | [Name] | [Name] | CTO |
| Database Admin | [Name] | [Name] | DevOps Lead |

**Contact Methods:**
- PagerDuty: Automatic escalation
- Slack: #oncall channel
- Phone: Emergency hotline

## Rollback Authority

Who can authorize a rollback:

| Severity | Authorized By |
|----------|--------------|
| P0 (Critical) | Any on-call engineer |
| P1 (High) | Engineering Lead or above |
| P2 (Medium) | Engineering Manager approval required |
| P3 (Low) | Product Owner + Engineering Manager |

## Version Control

After successful rollback:

```bash
# Tag the rollback point
git tag -a "rollback-pagination-$(date +%Y%m%d)" -m "Rolled back pagination feature"
git push origin rollback-pagination-$(date +%Y%m%d)

# Create issue for re-deployment
gh issue create --title "Re-deploy pagination after fix" \
  --body "Rollback performed on $(date). Fix and redeploy."
```

## Appendix

### A. Common Rollback Scenarios

**Scenario 1: High Invalid Cursor Rate**
- **Symptom**: 20% of requests returning HTTP 400
- **Procedure**: Procedure 3 (Feature Flag)
- **Reason**: Configuration or client compatibility issue

**Scenario 2: Database Connection Exhaustion**
- **Symptom**: "Too many connections" errors
- **Procedure**: Procedure 1 (Application-Only)
- **Reason**: Connection pool configuration issue

**Scenario 3: Memory Leak**
- **Symptom**: OOM errors after several hours
- **Procedure**: Procedure 1 (Application-Only)
- **Reason**: Cursor cache not cleaning up

### B. Rollback Verification Checklist

After rollback, verify:

- [ ] Health endpoint returns 200
- [ ] All API endpoints functional
- [ ] Error rate <1%
- [ ] Response time p95 <500ms
- [ ] Database queries working
- [ ] Authentication functional
- [ ] No errors in application logs
- [ ] No errors in database logs
- [ ] Metrics collecting properly
- [ ] Monitoring dashboards showing normal levels

### C. Communication Templates

**Customer Email (if needed):**
```
Subject: Brief API Service Disruption - Resolved

Dear Valued Customer,

We experienced a brief service disruption today from 14:15-14:35 UTC
due to a recent feature deployment. The issue has been resolved and
all services are now operating normally.

Impact:
- Duration: 20 minutes
- Affected: [specific endpoints]
- Data loss: None

We apologize for any inconvenience. If you have questions or concerns,
please contact support@example.com.

Best regards,
[Team Name]
```

---

**Last Updated**: October 15, 2025
**Next Review**: October 22, 2025
**Maintained By**: DevOps Team
