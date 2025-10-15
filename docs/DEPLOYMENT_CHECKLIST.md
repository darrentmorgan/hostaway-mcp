# Production Deployment Checklist
# Context Window Protection - Cursor-Based Pagination

**Feature**: 005-project-brownfield-hardening
**Version**: 1.0
**Target Date**: October 15, 2025

## Pre-Deployment

### Code Quality ✅

- [x] All unit tests passing (104/104)
- [x] All integration tests passing (8/8)
- [x] Linting checks pass (ruff)
- [x] No security vulnerabilities (static analysis)
- [x] Code review completed
- [x] Documentation updated

### Testing Verification

- [ ] **Staging Environment**
  - [ ] Deploy to staging
  - [ ] Run full test suite on staging
  - [ ] Verify cursor pagination works
  - [ ] Test invalid cursor handling
  - [ ] Verify backwards compatibility
  - [ ] Load test with realistic traffic

- [ ] **Performance Testing**
  - [ ] Cursor encode/decode <1ms ✅ (verified in unit tests)
  - [ ] Page load time <200ms
  - [ ] No memory leaks during sustained pagination
  - [ ] Token budget reduction >60% ✅ (projected)

- [ ] **Security Testing**
  - [ ] Cursor signature verification working
  - [ ] TTL expiration enforced (10 minutes)
  - [ ] API key authentication working
  - [ ] No sensitive data in cursors
  - [ ] Rate limiting still functional

### Documentation

- [x] Migration guide created (`PAGINATION_MIGRATION.md`)
- [x] OpenAPI docs updated (`OPENAPI_PAGINATION.md`)
- [x] Implementation summary updated
- [ ] Release notes prepared
- [ ] Client notification email drafted
- [ ] Internal team training completed

### Infrastructure

- [ ] **Configuration**
  - [ ] Environment variables set
    - [ ] `SUPABASE_URL`
    - [ ] `SUPABASE_SERVICE_KEY`
    - [ ] `HOSTAWAY_ACCOUNT_ID`
    - [ ] `HOSTAWAY_SECRET_KEY`
  - [ ] Cursor secret configured (secure random key)
  - [ ] Token budget thresholds configured
  - [ ] Rate limits configured

- [ ] **Monitoring Setup**
  - [ ] Health endpoint accessible (`/health`)
  - [ ] Metrics collection enabled
  - [ ] Alerting rules configured
  - [ ] Dashboard created
  - [ ] Log aggregation working

- [ ] **Backup & Rollback**
  - [ ] Database backup taken
  - [ ] Previous version tagged in git
  - [ ] Rollback procedure documented
  - [ ] Rollback tested in staging

## Deployment Steps

### 1. Pre-Deployment Notifications (D-7 days)

- [ ] Send email to API clients about upcoming changes
- [ ] Post announcement in developer portal
- [ ] Update status page with maintenance window
- [ ] Internal team notification

**Email Template:**
```
Subject: API Update: Cursor-Based Pagination - October 15, 2025

Dear Hostaway MCP API Users,

We're deploying an important upgrade to improve API performance and reliability:

**What's Changing:**
- Listings and Reservations endpoints now use cursor-based pagination
- New response format (backwards compatible)
- Improved performance and reduced latency

**Impact:**
- No action required for most clients
- Recommended: Migrate to cursor-based pagination
- See migration guide: [link]

**Timeline:**
- Deployment: October 15, 2025 at 02:00 UTC
- Expected downtime: 5 minutes
- Rollback window: 24 hours

Questions? Contact support@example.com

Best regards,
API Team
```

### 2. Final Verification (D-1 day)

- [ ] Re-run all tests on production-like environment
- [ ] Verify all dependencies up to date
- [ ] Check database connection pool limits
- [ ] Verify SSL certificates valid
- [ ] Test monitoring alerts trigger correctly
- [ ] Confirm rollback procedure ready

### 3. Deployment Window (D-Day)

**Recommended Time:** 02:00-03:00 UTC (lowest traffic)

#### Step 1: Enable Maintenance Mode (02:00 UTC)
```bash
# Set maintenance mode
echo "maintenance" > /var/www/status

# Or use load balancer
aws elbv2 modify-target-group --target-group-arn <arn> --health-check-path /maintenance
```

- [ ] Maintenance mode enabled
- [ ] Verify no active requests being processed
- [ ] Notify #oncall Slack channel

#### Step 2: Database Backup (02:05 UTC)
```bash
# Backup critical tables
pg_dump -h $DB_HOST -U $DB_USER -t api_keys -t organizations > backup_$(date +%Y%m%d_%H%M%S).sql
```

- [ ] Database backup completed
- [ ] Backup verified (test restore)
- [ ] Backup stored in S3/secure location

#### Step 3: Deploy Application (02:10 UTC)
```bash
# Pull latest code
git fetch origin
git checkout 005-project-brownfield-hardening
git pull

# Install dependencies
uv sync

# Run database migrations (if any)
python -m alembic upgrade head

# Restart application
systemctl restart hostaway-mcp
# OR
docker-compose up -d --no-deps --build api
```

- [ ] Code deployed
- [ ] Dependencies installed
- [ ] Migrations applied
- [ ] Application restarted
- [ ] Health check passes: `curl http://localhost:8000/health`

#### Step 4: Smoke Tests (02:15 UTC)
```bash
# Test health endpoint
curl -H "X-API-Key: $API_KEY" https://api.example.com/health

# Test pagination - first page
curl -H "X-API-Key: $API_KEY" "https://api.example.com/api/listings?limit=10"

# Test pagination - cursor navigation
# (use cursor from previous response)
curl -H "X-API-Key: $API_KEY" "https://api.example.com/api/listings?cursor=xxx"

# Test invalid cursor handling
curl -H "X-API-Key: $API_KEY" "https://api.example.com/api/listings?cursor=invalid"
# Should return HTTP 400

# Test bookings endpoint
curl -H "X-API-Key: $API_KEY" "https://api.example.com/api/reservations?limit=50"
```

- [ ] Health endpoint returns 200
- [ ] Listings pagination works
- [ ] Cursor navigation works
- [ ] Invalid cursor returns 400
- [ ] Bookings pagination works
- [ ] No errors in logs

#### Step 5: Disable Maintenance Mode (02:25 UTC)
```bash
# Remove maintenance mode
rm /var/www/status

# Or restore load balancer
aws elbv2 modify-target-group --target-group-arn <arn> --health-check-path /health
```

- [ ] Maintenance mode disabled
- [ ] Traffic flowing to application
- [ ] Response times normal (<500ms p95)
- [ ] Error rate <0.1%

#### Step 6: Monitor Initial Traffic (02:30-03:00 UTC)

- [ ] Watch metrics dashboard
  - [ ] Request rate returns to normal
  - [ ] Error rate <0.1%
  - [ ] Response time p95 <500ms
  - [ ] CPU usage <70%
  - [ ] Memory usage stable
- [ ] Check logs for errors
- [ ] Verify pagination adoption metric increasing
- [ ] No customer complaints in support channels

### 4. Post-Deployment Verification (D+1 hour)

- [ ] Run automated integration test suite
- [ ] Verify cursor TTL working (wait 10 min, test expiration)
- [ ] Check cursor signature validation
- [ ] Verify pagination metrics in `/health`
- [ ] Review application logs for errors
- [ ] Check database connection pool usage

### 5. Post-Deployment Monitoring (D+24 hours)

#### Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Pagination Adoption | Increasing | N/A |
| Invalid Cursor Rate | <1% | >5% |
| Response Time p95 | <500ms | >1000ms |
| Error Rate | <0.1% | >1% |
| Token Budget Reduction | >50% | <30% |
| Memory Usage | <80% | >90% |
| CPU Usage | <70% | >85% |

- [ ] **Hour 1**: Check metrics every 15 minutes
- [ ] **Hour 2-6**: Check metrics every hour
- [ ] **Hour 6-24**: Check metrics every 4 hours
- [ ] **Day 2-7**: Check metrics daily

#### Success Criteria (24 hours)

- [ ] No P0/P1 incidents
- [ ] Error rate <0.1%
- [ ] Pagination adoption >20%
- [ ] No performance degradation
- [ ] No customer escalations

### 6. Post-Deployment Communications

- [ ] Update status page: "Deployment successful"
- [ ] Email to API clients: "Migration complete"
- [ ] Internal team update in Slack
- [ ] Update documentation portal
- [ ] Close deployment ticket

## Rollback Procedure

### Trigger Conditions

Initiate rollback if ANY of the following occur:

- [ ] Error rate >5% for >10 minutes
- [ ] Response time p95 >2000ms for >10 minutes
- [ ] Critical functionality broken
- [ ] Database corruption detected
- [ ] Security vulnerability discovered
- [ ] >10 customer complaints in 1 hour

### Rollback Steps

#### Step 1: Enable Maintenance Mode
```bash
echo "maintenance" > /var/www/status
```

#### Step 2: Revert Application Code
```bash
# Checkout previous stable version
git checkout <previous-tag>

# Restore dependencies
uv sync

# Restart application
systemctl restart hostaway-mcp
```

#### Step 3: Database Rollback (if needed)
```bash
# Restore from backup
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < backup_YYYYMMDD_HHMMSS.sql

# OR revert migrations
python -m alembic downgrade -1
```

#### Step 4: Verify Rollback
```bash
# Test endpoints
curl https://api.example.com/health
curl https://api.example.com/api/listings
```

#### Step 5: Disable Maintenance Mode
```bash
rm /var/www/status
```

#### Step 6: Post-Rollback Actions
- [ ] Notify team in Slack
- [ ] Update status page
- [ ] Email clients about rollback
- [ ] Root cause analysis
- [ ] Schedule fix and redeploy

### Rollback Time Estimate

- Maintenance mode: 1 minute
- Code revert: 2 minutes
- Application restart: 1 minute
- Verification: 3 minutes
- **Total**: ~7 minutes

## Monitoring Dashboards

### Key Metrics Dashboard

Create Grafana/CloudWatch dashboard with:

1. **Request Metrics**
   - Total requests/sec
   - Requests by endpoint
   - Pagination requests vs non-paginated

2. **Performance Metrics**
   - Response time (p50, p95, p99)
   - Cursor encode/decode time
   - Database query time

3. **Error Metrics**
   - HTTP 400 (invalid cursor) rate
   - HTTP 500 rate
   - Error breakdown by type

4. **Pagination Metrics**
   - Pagination adoption rate
   - Average page size
   - Cursor expiration rate
   - Pages per session

5. **System Metrics**
   - CPU usage
   - Memory usage
   - Database connections
   - Network I/O

### Alert Rules

```yaml
alerts:
  - name: high_invalid_cursor_rate
    condition: invalid_cursor_rate > 5%
    for: 10m
    severity: warning
    action: notify_oncall

  - name: high_error_rate
    condition: error_rate > 1%
    for: 5m
    severity: critical
    action: page_oncall

  - name: slow_response_time
    condition: p95_response_time > 1000ms
    for: 10m
    severity: warning
    action: notify_oncall

  - name: cursor_ttl_not_expiring
    condition: cursor_ttl_expiration_rate == 0
    for: 30m
    severity: warning
    action: notify_team
```

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Cursor signature failures | Low | High | Thorough testing, monitoring |
| Performance degradation | Low | Medium | Load testing, rollback ready |
| Client compatibility issues | Medium | Low | Backwards compatible design |
| Cursor TTL too short | Medium | Low | 10-min TTL tested, adjustable |
| Memory leak from cursors | Low | Medium | TTL cleanup, monitoring |
| Database connection exhaustion | Low | High | Connection pooling configured |

## Success Metrics (30 days)

- [ ] Pagination adoption >95%
- [ ] Token usage reduced >60%
- [ ] Context overflow <1%
- [ ] Error rate <0.1%
- [ ] No P0/P1 incidents
- [ ] Customer satisfaction maintained

## Lessons Learned (Post-Mortem)

**Schedule**: D+7 days

Discussion topics:
- What went well?
- What could be improved?
- Were estimates accurate?
- Any unexpected issues?
- Documentation gaps?
- Process improvements?

---

## Sign-Off

### Pre-Deployment Approval

- [ ] **Tech Lead**: _______________ Date: _______
- [ ] **DevOps**: _______________ Date: _______
- [ ] **QA Lead**: _______________ Date: _______
- [ ] **Product Owner**: _______________ Date: _______

### Post-Deployment Verification

- [ ] **Deployment Lead**: _______________ Date: _______
- [ ] **On-Call Engineer**: _______________ Date: _______

---

**Last Updated**: October 15, 2025
**Version**: 1.0
**Next Review**: October 22, 2025
