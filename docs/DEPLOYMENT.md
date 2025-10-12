# Deployment Runbook - Hostaway MCP Server

**Version**: 0.1.0
**Last Updated**: 2025-10-12
**Status**: Production Ready

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Deployment Methods](#deployment-methods)
4. [Post-Deployment Validation](#post-deployment-validation)
5. [Rollback Procedures](#rollback-procedures)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### 1. Code Quality Validation

```bash
# Run all checks locally before deploying
cd /path/to/hostaway-mcp

# 1. Run linting
uv run ruff format --check .
uv run ruff check .

# 2. Run type checking
uv run mypy src/

# 3. Run full test suite
uv run pytest --cov=src --cov-fail-under=80

# 4. Run security scan
uv run bandit -r src/ -f json -o security-report.json
```

**Expected Results**:
- ✅ All linting checks pass
- ✅ No mypy type errors
- ✅ All 124 tests passing
- ✅ Coverage ≥ 72.80% (target: 80%)
- ✅ No critical security issues

### 2. Configuration Validation

**Required Environment Variables**:
```bash
# Verify all required variables are set
cat .env.example

# Required:
HOSTAWAY_CLIENT_ID=<your_client_id>
HOSTAWAY_CLIENT_SECRET=<your_client_secret>
HOSTAWAY_BASE_URL=https://api.hostaway.com/v1

# Optional (with defaults):
RATE_LIMIT_IP=15              # req/10s per IP
RATE_LIMIT_ACCOUNT=20         # req/10s per account
MAX_CONCURRENT_REQUESTS=10    # concurrent request limit
TOKEN_REFRESH_DAYS=7          # proactive token refresh
```

### 3. Security Checklist

- [ ] Credentials stored in secret manager (not .env files)
- [ ] TLS/HTTPS configured on reverse proxy
- [ ] CORS origins restricted (not `["*"]`)
- [ ] Rate limiting configured appropriately
- [ ] Logging configured (no sensitive data)
- [ ] Health check endpoint accessible
- [ ] Security headers configured (CSP, X-Frame-Options)
- [ ] Firewall rules configured (port 8000 internal only)

### 4. Infrastructure Readiness

- [ ] Docker/Kubernetes cluster ready
- [ ] Reverse proxy configured (nginx/traefik)
- [ ] SSL certificates provisioned
- [ ] Load balancer configured
- [ ] Monitoring/logging stack deployed
- [ ] Backup/disaster recovery plan documented

---

## Environment Setup

### Development Environment

```bash
# 1. Clone repository
git clone https://github.com/yourusername/hostaway-mcp.git
cd hostaway-mcp

# 2. Install dependencies
uv sync

# 3. Copy environment template
cp .env.example .env

# 4. Configure credentials
# Edit .env with your Hostaway API credentials

# 5. Run locally
uv run uvicorn src.api.main:app --reload
```

**Validation**:
- Server starts on http://localhost:8000
- OpenAPI docs available at http://localhost:8000/docs
- Health check passes: `curl http://localhost:8000/health`

### Staging Environment

```bash
# 1. Use docker-compose for staging
docker-compose up -d

# 2. Verify deployment
docker ps | grep hostaway-mcp
docker logs hostaway-mcp-server

# 3. Run smoke tests
pytest tests/e2e/ -v
```

### Production Environment

**Option A: Docker Deployment** (Recommended)

```bash
# 1. Build production image
docker build -t hostaway-mcp:0.1.0 .

# 2. Tag for registry
docker tag hostaway-mcp:0.1.0 registry.example.com/hostaway-mcp:0.1.0

# 3. Push to registry
docker push registry.example.com/hostaway-mcp:0.1.0

# 4. Deploy to production
docker run -d \
  --name hostaway-mcp \
  -p 8000:8000 \
  --env-file /secure/path/to/.env \
  --restart unless-stopped \
  registry.example.com/hostaway-mcp:0.1.0
```

**Option B: Kubernetes Deployment**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hostaway-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hostaway-mcp
  template:
    metadata:
      labels:
        app: hostaway-mcp
    spec:
      containers:
      - name: hostaway-mcp
        image: registry.example.com/hostaway-mcp:0.1.0
        ports:
        - containerPort: 8000
        env:
        - name: HOSTAWAY_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: hostaway-secrets
              key: client-id
        - name: HOSTAWAY_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: hostaway-secrets
              key: client-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

---

## Deployment Methods

### Method 1: Docker Compose (Local/Staging)

```bash
# 1. Build and start
docker-compose up -d --build

# 2. View logs
docker-compose logs -f hostaway-mcp

# 3. Stop
docker-compose down
```

**Use Case**: Local development, staging environments

### Method 2: Docker Standalone (Production)

```bash
# 1. Pull latest image
docker pull registry.example.com/hostaway-mcp:0.1.0

# 2. Stop old container
docker stop hostaway-mcp
docker rm hostaway-mcp

# 3. Start new container
docker run -d \
  --name hostaway-mcp \
  -p 8000:8000 \
  --env-file /secure/.env \
  --restart unless-stopped \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  registry.example.com/hostaway-mcp:0.1.0

# 4. Verify health
curl http://localhost:8000/health
```

**Use Case**: Single-server production deployments

### Method 3: Kubernetes (Cloud/Scalable)

```bash
# 1. Create namespace
kubectl create namespace hostaway

# 2. Create secrets
kubectl create secret generic hostaway-secrets \
  --from-literal=client-id=$HOSTAWAY_CLIENT_ID \
  --from-literal=client-secret=$HOSTAWAY_CLIENT_SECRET \
  -n hostaway

# 3. Deploy application
kubectl apply -f k8s/ -n hostaway

# 4. Verify deployment
kubectl get pods -n hostaway
kubectl get svc -n hostaway

# 5. Port forward for testing
kubectl port-forward svc/hostaway-mcp 8000:8000 -n hostaway
```

**Use Case**: Cloud-native, auto-scaling production deployments

### Method 4: CI/CD Pipeline (Automated)

GitHub Actions workflow (`.github/workflows/deploy.yml`):

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push Docker image
        run: |
          docker build -t registry.example.com/hostaway-mcp:${{ github.ref_name }} .
          docker push registry.example.com/hostaway-mcp:${{ github.ref_name }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/hostaway-mcp \
            hostaway-mcp=registry.example.com/hostaway-mcp:${{ github.ref_name }} \
            -n hostaway
```

**Use Case**: Automated deployments on git tags

---

## Post-Deployment Validation

### 1. Health Check Validation

```bash
# Basic health check
curl http://production-url/health

# Expected response:
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-10-12T04:30:00Z"
}
```

### 2. Authentication Validation

```bash
# Test token acquisition
curl -X POST http://production-url/authenticate \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected: 200 OK with access_token
```

### 3. API Endpoint Validation

```bash
# Get OpenAPI docs
curl http://production-url/docs

# Test property listing
curl http://production-url/listings?limit=5

# Test booking search
curl "http://production-url/reservations?limit=10"
```

### 4. Performance Validation

```bash
# Run performance tests
pytest tests/performance/ -v

# Expected:
# - Authentication: < 5 seconds
# - API response: < 2 seconds
# - MCP tool invocation: < 1 second
# - 100 concurrent requests: no errors
```

### 5. MCP Tool Discovery

```bash
# Verify MCP tools are exposed
curl http://production-url/mcp/tools

# Expected: List of 15+ tools including:
# - list_all_properties
# - get_property_details
# - search_bookings
# - get_revenue_report
```

### 6. Log Validation

```bash
# Check structured logging
docker logs hostaway-mcp | head -n 20

# Expected JSON format with:
# - timestamp
# - level
# - correlation_id
# - message
```

### 7. Security Validation

```bash
# Check TLS/HTTPS
curl -I https://production-url/health

# Verify security headers
curl -I https://production-url/ | grep -E "(X-|Content-Security)"

# Expected headers:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# Content-Security-Policy: ...
```

### 8. Rate Limiting Validation

```bash
# Test rate limiting
for i in {1..20}; do
  curl http://production-url/listings &
done

# Expected: Some requests return 429 Too Many Requests
```

---

## Rollback Procedures

### Docker Rollback

```bash
# 1. Identify last working version
docker images | grep hostaway-mcp

# 2. Stop current container
docker stop hostaway-mcp

# 3. Start previous version
docker run -d \
  --name hostaway-mcp \
  -p 8000:8000 \
  --env-file /secure/.env \
  --restart unless-stopped \
  registry.example.com/hostaway-mcp:0.0.9  # previous version

# 4. Verify rollback
curl http://localhost:8000/health
```

### Kubernetes Rollback

```bash
# 1. Check deployment history
kubectl rollout history deployment/hostaway-mcp -n hostaway

# 2. Rollback to previous version
kubectl rollout undo deployment/hostaway-mcp -n hostaway

# 3. Rollback to specific revision
kubectl rollout undo deployment/hostaway-mcp \
  --to-revision=2 \
  -n hostaway

# 4. Verify rollback
kubectl rollout status deployment/hostaway-mcp -n hostaway
```

### Database/Schema Rollback

**Note**: This application does NOT use a database. All data comes from Hostaway API.

If you add a database in the future:
```bash
# Use Alembic for schema migrations
alembic downgrade -1  # rollback one migration
alembic downgrade <revision>  # rollback to specific version
```

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Application Metrics**:
   - Request rate (req/s)
   - Response time (p50, p95, p99)
   - Error rate (4xx, 5xx)
   - Token refresh success rate

2. **Infrastructure Metrics**:
   - CPU usage (target: < 70%)
   - Memory usage (target: < 80%)
   - Network I/O
   - Disk I/O

3. **Business Metrics**:
   - MCP tool invocations/hour
   - Authentication attempts/hour
   - API endpoint usage distribution

### Prometheus Metrics (Future Enhancement)

```python
# src/mcp/metrics.py (to be added)
from prometheus_client import Counter, Histogram, Gauge

request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_tokens = Gauge('active_tokens_total', 'Number of active tokens')
```

### Alerting Rules

**Critical Alerts** (page immediately):
- Application down (health check fails)
- Error rate > 5%
- Authentication failing (> 50% failure rate)

**Warning Alerts** (notify):
- Response time > 3 seconds (p95)
- Memory usage > 80%
- Rate limit hit frequently (> 100/min)

**Info Alerts** (log):
- Token refresh occurred
- New version deployed
- Configuration change

### Log Aggregation

Configure log shipping to centralized logging:

```yaml
# docker-compose.yml (with logging)
services:
  hostaway-mcp:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "app=hostaway-mcp,env=production"
```

Integrate with:
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Grafana Loki**: For Kubernetes deployments
- **CloudWatch Logs**: For AWS deployments

---

## Troubleshooting

### Issue 1: Server Won't Start

**Symptoms**: Container exits immediately or server fails to bind port

**Diagnosis**:
```bash
# Check logs
docker logs hostaway-mcp

# Check port availability
lsof -i :8000
```

**Solutions**:
1. Port already in use → Change port or kill conflicting process
2. Missing environment variables → Verify .env file
3. Invalid credentials → Check Hostaway API credentials

### Issue 2: Authentication Failures

**Symptoms**: 401 Unauthorized, token refresh failures

**Diagnosis**:
```bash
# Check token manager logs
docker logs hostaway-mcp | grep "TokenManager"

# Test credentials manually
curl -X POST https://api.hostaway.com/v1/accessTokens \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "scope": "general"
  }'
```

**Solutions**:
1. Invalid credentials → Regenerate from Hostaway dashboard
2. Token expired → Force refresh: `curl /refresh_token`
3. Rate limited → Wait 10 seconds, retry

### Issue 3: Slow API Responses

**Symptoms**: Response times > 3 seconds

**Diagnosis**:
```bash
# Check performance metrics
pytest tests/performance/test_load.py -v

# Profile specific endpoint
time curl http://localhost:8000/listings
```

**Solutions**:
1. Increase connection pool size (edit config.py)
2. Enable HTTP/2 on reverse proxy
3. Add caching layer (Redis)
4. Increase rate limits if bottleneck

### Issue 4: Rate Limit Exceeded

**Symptoms**: 429 Too Many Requests

**Diagnosis**:
```bash
# Check rate limiter logs
docker logs hostaway-mcp | grep "RateLimiter"
```

**Solutions**:
1. Increase rate limits in .env:
   ```
   RATE_LIMIT_IP=30
   RATE_LIMIT_ACCOUNT=50
   ```
2. Implement exponential backoff in client
3. Use batch endpoints where available

### Issue 5: Memory Leak

**Symptoms**: Memory usage grows over time, OOM kills

**Diagnosis**:
```bash
# Monitor memory usage
docker stats hostaway-mcp

# Check for connection leaks
netstat -an | grep 8000 | wc -l
```

**Solutions**:
1. Ensure httpx client cleanup (already implemented in `aclose()`)
2. Add memory limits in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 512M
   ```
3. Restart container periodically if leak persists

### Issue 6: CORS Errors

**Symptoms**: Browser blocks requests, preflight failures

**Diagnosis**:
```bash
# Check CORS configuration
curl -I http://localhost:8000/listings \
  -H "Origin: https://example.com"
```

**Solutions**:
1. Update CORS origins in `src/api/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://allowed-domain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

## Production Deployment Checklist

**Final Pre-Launch Checklist**:

- [ ] All tests passing (124/124)
- [ ] Security audit complete (no critical issues)
- [ ] Code review approved (93/100 score)
- [ ] Environment variables configured
- [ ] Secrets stored in secret manager
- [ ] TLS/HTTPS configured
- [ ] CORS restricted to production domains
- [ ] Rate limiting configured appropriately
- [ ] Monitoring and alerting configured
- [ ] Log aggregation configured
- [ ] Backup/disaster recovery plan documented
- [ ] Rollback procedure tested
- [ ] Runbook reviewed with team
- [ ] On-call rotation established
- [ ] Staging deployment validated
- [ ] Performance benchmarks met
- [ ] Load testing completed (100+ concurrent)
- [ ] MCP tool discovery verified
- [ ] Documentation up to date
- [ ] Change management approval obtained

**Post-Launch Validation** (within 1 hour):

- [ ] Health check passing
- [ ] Authentication working
- [ ] All API endpoints responding
- [ ] Logs appearing in aggregation system
- [ ] Metrics visible in monitoring
- [ ] No error spikes
- [ ] Response times within SLA
- [ ] MCP tools discoverable by Claude Desktop

**Post-Launch Monitoring** (first 24 hours):

- [ ] Monitor error rates (target: < 1%)
- [ ] Monitor response times (target: p95 < 2s)
- [ ] Monitor resource usage (CPU < 70%, Memory < 80%)
- [ ] Review logs for unexpected errors
- [ ] Validate rate limiting effectiveness
- [ ] Confirm authentication stability

---

## Support & Escalation

**On-Call Rotation**: TBD
**Escalation Path**: TBD
**Incident Response**: Follow incident response runbook (docs/INCIDENT_RESPONSE.md)

**Contact Information**:
- Primary: oncall@example.com
- Secondary: engineering@example.com
- Hostaway Support: support@hostaway.com

---

## Appendix

### A. Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HOSTAWAY_CLIENT_ID` | Yes | - | Hostaway API client ID |
| `HOSTAWAY_CLIENT_SECRET` | Yes | - | Hostaway API client secret |
| `HOSTAWAY_BASE_URL` | No | `https://api.hostaway.com/v1` | Hostaway API base URL |
| `RATE_LIMIT_IP` | No | `15` | Requests per 10s per IP |
| `RATE_LIMIT_ACCOUNT` | No | `20` | Requests per 10s per account |
| `MAX_CONCURRENT_REQUESTS` | No | `10` | Max concurrent requests |
| `TOKEN_REFRESH_DAYS` | No | `7` | Days before expiry to refresh token |

### B. API Endpoints

All endpoints require authentication via `get_authenticated_client()` dependency.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (no auth required) |
| `/authenticate` | POST | Manual token acquisition |
| `/refresh_token` | POST | Manual token refresh |
| `/listings` | GET | List all properties |
| `/listings/{id}` | GET | Get property details |
| `/listings/{id}/availability` | GET | Check property availability |
| `/reservations` | GET | Search bookings |
| `/reservations/{id}` | GET | Get booking details |
| `/reservations/{id}/guest` | GET | Get guest info for booking |
| `/financialReports` | GET | Get financial report |

### C. Docker Image Tags

- `latest` - Latest stable release
- `0.1.0` - Specific version (production)
- `develop` - Development branch (staging only)
- `sha-<commit>` - Specific commit (debugging)

### D. Useful Commands

```bash
# View all routes
curl http://localhost:8000/openapi.json | jq '.paths | keys'

# View MCP tool definitions
curl http://localhost:8000/mcp/tools | jq '.'

# Test authentication flow
curl -X POST http://localhost:8000/authenticate

# Stream logs with correlation ID filtering
docker logs -f hostaway-mcp | grep "correlation_id"

# Check resource usage
docker stats hostaway-mcp --no-stream

# Export metrics (when Prometheus added)
curl http://localhost:8000/metrics
```

---

**Document Version**: 1.0
**Last Review**: 2025-10-12
**Next Review**: 2025-11-12
**Owner**: Engineering Team
