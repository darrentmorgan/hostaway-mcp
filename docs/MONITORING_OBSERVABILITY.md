# Monitoring & Observability Guide
# Context Window Protection - Cursor-Based Pagination

**Version**: 1.0
**Date**: October 15, 2025

## Overview

This guide covers monitoring and observability for the cursor-based pagination feature, including metrics collection, dashboards, alerting, and troubleshooting.

## Health Endpoint

The `/health` endpoint provides real-time metrics about the pagination system.

### Endpoint

```
GET /health
```

**No authentication required** (public endpoint for monitoring)

### Response

```json
{
  "status": "healthy",
  "timestamp": "2025-10-15T14:32:10.123456Z",
  "version": "0.1.0",
  "service": "hostaway-mcp",
  "context_protection": {
    "total_requests": 15234,
    "pagination_adoption": 0.87,
    "summarization_adoption": 0.45,
    "avg_response_size_bytes": 2400,
    "avg_latency_ms": 145.2,
    "oversized_events": 12,
    "uptime_seconds": 86400
  }
}
```

### Metrics Explained

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `total_requests` | Counter | Total API requests processed | N/A |
| `pagination_adoption` | Rate (0-1) | % of requests using pagination | >0.95 |
| `summarization_adoption` | Rate (0-1) | % of responses summarized | >0.70 |
| `avg_response_size_bytes` | Gauge | Average response size | <2500 |
| `avg_latency_ms` | Gauge | Average response time | <200 |
| `oversized_events` | Counter | Responses exceeding token budget | <100/day |
| `uptime_seconds` | Counter | Service uptime | N/A |

### Monitoring Health Endpoint

```bash
# Manual check
curl https://api.example.com/health | jq .

# Automated monitoring (every 60s)
watch -n 60 'curl -s https://api.example.com/health | jq .context_protection'

# Prometheus scraping
curl https://api.example.com/health | jq -r '.context_protection | to_entries | .[] | "\(.key) \(.value)"'
```

## Metrics Collection

### Built-in Telemetry Service

The application includes a telemetry service (`src/services/telemetry_service.py`) that tracks:

1. **Request Counters**
   - Total requests
   - Paginated vs non-paginated requests
   - Summarized vs full responses

2. **Performance Metrics**
   - Response times (histogram)
   - Response sizes (histogram)
   - Cursor encode/decode times

3. **Error Tracking**
   - Invalid cursor attempts
   - Token budget exceeded events
   - API errors by type

### Accessing Metrics

```python
from src.services.telemetry_service import get_telemetry_service

telemetry = get_telemetry_service()
metrics = telemetry.get_metrics()

print(f"Total requests: {metrics['total_requests']}")
print(f"Pagination adoption: {metrics['pagination_adoption']:.1%}")
print(f"Avg response size: {metrics['avg_response_size']:.0f} bytes")
```

## Log Aggregation

### Structured Logging

All logs are output in JSON format for easy parsing:

```json
{
  "timestamp": "2025-10-15T14:32:10.123456Z",
  "level": "INFO",
  "logger": "src.api.routes.listings",
  "message": "Cursor pagination requested",
  "extra": {
    "correlation_id": "abc123",
    "endpoint": "/api/listings",
    "cursor_present": true,
    "limit": 50,
    "duration_ms": 145
  }
}
```

### Log Levels

| Level | Usage | Examples |
|-------|-------|----------|
| DEBUG | Development debugging | Cursor encoding details |
| INFO | Normal operations | API requests, pagination events |
| WARNING | Recoverable issues | Invalid cursors, high load |
| ERROR | Error conditions | Database failures, auth errors |
| CRITICAL | System failures | Service unavailable |

### Key Log Events

#### Pagination Events

```json
{
  "event": "pagination_requested",
  "endpoint": "/api/listings",
  "limit": 50,
  "cursor_provided": true
}
```

```json
{
  "event": "cursor_encoded",
  "offset": 50,
  "encode_time_ms": 0.5
}
```

```json
{
  "event": "cursor_decoded",
  "offset": 50,
  "decode_time_ms": 0.6
}
```

#### Error Events

```json
{
  "event": "invalid_cursor",
  "reason": "Signature verification failed",
  "client_ip": "192.168.1.100"
}
```

```json
{
  "event": "cursor_expired",
  "age_minutes": 15,
  "client_ip": "192.168.1.100"
}
```

### Log Queries (Examples)

#### Find all invalid cursor attempts (last hour)
```bash
# Using grep
grep "invalid_cursor" application.log | jq 'select(.timestamp > (now - 3600))'

# Using jq
jq 'select(.event == "invalid_cursor")' application.log

# Using CloudWatch Insights
fields @timestamp, @message
| filter event = "invalid_cursor"
| sort @timestamp desc
| limit 100
```

#### Track pagination adoption over time
```bash
# Group by hour
jq -r 'select(.event == "pagination_requested") | .timestamp' application.log | \
  cut -d'T' -f2 | cut -d':' -f1 | sort | uniq -c
```

## Dashboards

### Grafana Dashboard Setup

#### Data Source: Prometheus

**Prometheus Configuration** (`prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'hostaway-mcp'
    scrape_interval: 30s
    metrics_path: '/metrics'  # If Prometheus exporter added
    static_configs:
      - targets: ['localhost:8000']

  # Or scrape health endpoint
  - job_name: 'hostaway-mcp-health'
    scrape_interval: 60s
    metrics_path: '/health'
    static_configs:
      - targets: ['localhost:8000']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'context_protection_(.*)'
        target_label: __name__
        replacement: 'hostaway_${1}'
```

#### Dashboard Panels

**1. Request Volume**
```promql
# Total requests per minute
rate(hostaway_total_requests[1m])

# Paginated vs non-paginated
rate(hostaway_paginated_requests[1m])
rate(hostaway_non_paginated_requests[1m])
```

**2. Pagination Adoption**
```promql
# Adoption rate (%)
(hostaway_paginated_requests / hostaway_total_requests) * 100
```

**3. Response Time**
```promql
# Average response time
histogram_quantile(0.95, rate(hostaway_response_time_bucket[5m]))

# By endpoint
histogram_quantile(0.95, rate(hostaway_response_time_bucket{endpoint="/api/listings"}[5m]))
```

**4. Error Rate**
```promql
# Invalid cursor rate
rate(hostaway_invalid_cursor_total[1m])

# Overall error rate
rate(hostaway_errors_total[1m]) / rate(hostaway_total_requests[1m])
```

**5. Token Budget Usage**
```promql
# Average response size
avg(hostaway_response_size_bytes)

# Oversized responses
rate(hostaway_oversized_events[1m])
```

### CloudWatch Dashboard (AWS)

**Metrics to Track:**

1. **Custom Metrics** (via CloudWatch SDK):
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='HostawayMCP',
    MetricData=[
        {
            'MetricName': 'PaginationAdoption',
            'Value': metrics['pagination_adoption'],
            'Unit': 'Percent',
            'Timestamp': datetime.now(UTC)
        },
        {
            'MetricName': 'AvgResponseSize',
            'Value': metrics['avg_response_size'],
            'Unit': 'Bytes',
            'Timestamp': datetime.now(UTC)
        }
    ]
)
```

2. **Application Logs** (via CloudWatch Logs):
```python
import watchtower

logger.addHandler(watchtower.CloudWatchLogHandler(
    log_group='/aws/hostaway-mcp',
    stream_name='pagination'
))
```

### Datadog Dashboard

**Integration:**
```python
from datadog import initialize, statsd

initialize(
    api_key='your-api-key',
    app_key='your-app-key'
)

# Track metrics
statsd.increment('hostaway.pagination.requests')
statsd.histogram('hostaway.response.size', response_size)
statsd.gauge('hostaway.adoption.rate', adoption_rate)
```

**Dashboard Widgets:**
- Timeseries: Request volume over time
- Query value: Current pagination adoption %
- Heatmap: Response time distribution
- Top list: Most common error types

## Alerting

### Alert Rules

#### 1. High Invalid Cursor Rate
```yaml
alert: HighInvalidCursorRate
expr: |
  (
    rate(hostaway_invalid_cursor_total[5m])
    /
    rate(hostaway_total_requests[5m])
  ) > 0.05
for: 10m
severity: warning
annotations:
  summary: "High invalid cursor rate detected"
  description: "{{ $value | humanizePercentage }} of requests have invalid cursors"
action:
  - notify: slack-oncall
  - create: jira-ticket
```

#### 2. Pagination Adoption Too Low
```yaml
alert: LowPaginationAdoption
expr: hostaway_pagination_adoption < 0.20
for: 24h
severity: info
annotations:
  summary: "Pagination adoption below target"
  description: "Only {{ $value | humanizePercentage }} of clients using pagination"
action:
  - notify: slack-team
```

#### 3. High Token Budget Overruns
```yaml
alert: FrequentOversizedResponses
expr: rate(hostaway_oversized_events[1h]) > 10
for: 1h
severity: warning
annotations:
  summary: "Too many oversized responses"
  description: "{{ $value }} responses exceeded token budget in the last hour"
action:
  - notify: slack-oncall
```

#### 4. Cursor Encoding Performance
```yaml
alert: SlowCursorEncoding
expr: hostaway_cursor_encode_time_p95 > 5
for: 5m
severity: warning
annotations:
  summary: "Cursor encoding is slow"
  description: "p95 cursor encoding time is {{ $value }}ms (target: 1ms)"
action:
  - notify: slack-oncall
  - escalate: pagerduty
```

### Alert Channels

**Slack Integration:**
```python
import requests

def send_slack_alert(metric, value, threshold):
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

    message = {
        "text": f"🚨 Alert: {metric}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{metric}*\nCurrent: `{value}`\nThreshold: `{threshold}`"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Dashboard"},
                        "url": "https://grafana.example.com/d/pagination"
                    }
                ]
            }
        ]
    }

    requests.post(webhook_url, json=message)
```

**PagerDuty Integration:**
```python
import pypd

pypd.api_key = 'your-api-key'

def create_pagerduty_incident(title, description):
    incident = pypd.Incident.create(
        incident_key='pagination-alert',
        title=title,
        service=pypd.Service.find_one(name='Hostaway MCP'),
        urgency='high',
        body={'type': 'incident_body', 'details': description}
    )
```

## Tracing

### Distributed Tracing with OpenTelemetry

**Setup:**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Configure tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Export to Jaeger
jaeger_exporter = JaegerExporter(
    agent_host_name='localhost',
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)
```

**Instrument Pagination:**
```python
@tracer.start_as_current_span("encode_cursor")
def encode_cursor(offset: int, secret: str) -> str:
    span = trace.get_current_span()
    span.set_attribute("pagination.offset", offset)

    cursor = _do_encoding(offset, secret)

    span.set_attribute("pagination.cursor_length", len(cursor))
    return cursor
```

**View Traces:**
- Jaeger UI: `http://localhost:16686`
- Filter by operation: `encode_cursor`, `decode_cursor`
- Analyze latency breakdown

## Performance Profiling

### Python Profiling

**Profile cursor operations:**
```python
import cProfile
import pstats

# Profile encode/decode
profiler = cProfile.Profile()
profiler.enable()

for _ in range(1000):
    cursor = encode_cursor(offset=50, secret="test-secret")
    decode_cursor(cursor, secret="test-secret")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

**Memory profiling:**
```python
from memory_profiler import profile

@profile
def test_cursor_memory():
    cursors = []
    for i in range(10000):
        cursor = encode_cursor(offset=i, secret="test")
        cursors.append(cursor)
    return cursors
```

### Load Testing

**Locust load test:**
```python
from locust import HttpUser, task, between

class PaginationUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def fetch_listings_with_pagination(self):
        cursor = None

        for _ in range(5):  # Fetch 5 pages
            params = {"limit": 50}
            if cursor:
                params["cursor"] = cursor

            with self.client.get(
                "/api/listings",
                params=params,
                headers={"X-API-Key": "test-key"},
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    cursor = data.get("nextCursor")
                    response.success()
                else:
                    response.failure(f"Got status {response.status_code}")
```

**Run load test:**
```bash
locust -f locustfile.py --host=https://api.example.com --users=100 --spawn-rate=10
```

## Troubleshooting

### Common Issues

#### High Invalid Cursor Rate

**Symptoms:**
- Alert: `HighInvalidCursorRate`
- Logs show frequent "Invalid cursor" errors

**Diagnosis:**
```bash
# Check error distribution
jq 'select(.event == "invalid_cursor") | .reason' logs.json | sort | uniq -c

# Common reasons:
# - "Signature verification failed" (tampering or wrong secret)
# - "Cursor expired" (>10 min old)
# - "Invalid format" (malformed cursor)
```

**Resolution:**
- If "signature failed": Verify cursor secret matches across instances
- If "expired": Client may be caching cursors too long
- If "invalid format": Client may be URL-encoding incorrectly

#### Slow Response Times

**Symptoms:**
- Alert: `SlowResponseTime`
- p95 latency >1000ms

**Diagnosis:**
```bash
# Check response time breakdown
jq 'select(.event == "request_completed") | {endpoint: .endpoint, duration: .duration_ms}' logs.json | \
  jq -s 'group_by(.endpoint) | map({endpoint: .[0].endpoint, avg: (map(.duration) | add / length)})'
```

**Resolution:**
- Check database query performance
- Verify cursor cache hit rate
- Check if token estimation is slow

#### Memory Leak

**Symptoms:**
- Gradually increasing memory usage
- OOM errors

**Diagnosis:**
```python
# Check cursor storage size
from src.services.cursor_storage import get_cursor_storage

storage = get_cursor_storage()
print(f"Cached cursors: {len(storage._storage)}")
```

**Resolution:**
- Verify TTL cleanup is working
- Check for circular references
- Review cursor storage implementation

### Debug Mode

Enable debug logging for detailed pagination traces:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in config
LOG_LEVEL=DEBUG python -m src.api.main
```

Debug logs include:
- Cursor encoding/decoding details
- Token estimation breakdowns
- Cache hit/miss events
- Performance timing for each operation

---

**Last Updated**: October 15, 2025
**Maintained By**: DevOps Team
**Related Docs**: [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)
