# Quickstart Guide: Guest Communication & Enhanced Error Handling (v1.1)

**Date**: 2025-10-13
**Prerequisites**: v1.0 deployed and operational, MCP API key configured

---

## Overview

v1.1 adds three major capabilities to the Hostaway MCP Server:

1. **Message Search & History** - Retrieve guest conversations across all channels
2. **Partial Failure Handling** - Batch operations with graceful degradation
3. **Enhanced Test Coverage** - Comprehensive edge case and error path testing

This guide demonstrates how to use the new v1.1 features via MCP tools.

---

## Setup

### Prerequisites

- v1.0 Hostaway MCP Server deployed (http://72.60.233.157:8080)
- MCP API key configured in Claude Desktop:
  ```json
  {
    "mcpServers": {
      "hostaway-mcp": {
        "command": "/Users/darrenmorgan/.local/bin/uv",
        "args": ["run", "--directory", "/path/to/hostaway-mcp", "python", "mcp_stdio_server.py"],
        "env": {
          "REMOTE_MCP_URL": "http://72.60.233.157:8080",
          "REMOTE_MCP_API_KEY": "your-api-key-here"
        }
      }
    }
  }
  ```
- Valid Hostaway credentials (account ID, secret key)

### Verify v1.1 Deployment

```bash
# Check health endpoint
curl http://72.60.233.157:8080/health

# Expected response
{
  "status": "healthy",
  "version": "1.1.0",
  "features": ["messages", "batch_partial_failures"]
}
```

---

## Feature 1: Message Search & Conversation History

### Example 1.1: Search Messages by Booking ID

**Use Case**: Retrieve all messages for a specific booking to understand guest context.

**MCP Tool Invocation**:
```python
search_messages(booking_id=12345)
```

**Expected Response**:
```json
{
  "successful_results": [
    {
      "id": "msg_abc123",
      "booking_id": 12345,
      "content": "What time is check-in?",
      "timestamp": "2025-10-13T14:30:00Z",
      "channel": "platform",
      "sender_type": "guest",
      "sender_id": "guest_xyz",
      "recipient_id": "pm_789",
      "delivery_status": "delivered"
    },
    {
      "id": "msg_def456",
      "booking_id": 12345,
      "content": "Check-in is at 3 PM",
      "timestamp": "2025-10-13T15:00:00Z",
      "channel": "email",
      "sender_type": "property_manager",
      "sender_id": "pm_789",
      "recipient_id": "guest_xyz",
      "delivery_status": "read"
    }
  ],
  "failed_items": [],
  "summary": {
    "total_attempted": 1,
    "succeeded": 1,
    "failed": 0,
    "success_rate": 1.0
  }
}
```

**Interpretation**:
- 2 messages found for booking 12345
- Messages from multiple channels (platform + email) consolidated chronologically
- Guest asked question via Airbnb (platform), property manager replied via email

### Example 1.2: Search Messages by Guest Name

**Use Case**: Find all communications with a guest across multiple bookings.

**MCP Tool Invocation**:
```python
search_messages(guest_name="John Smith")
```

**Expected Response**:
```json
{
  "successful_results": [
    {
      "id": "msg_001",
      "booking_id": 12345,
      "content": "Looking forward to my stay!",
      "timestamp": "2025-10-10T10:00:00Z",
      "channel": "email",
      "sender_type": "guest",
      "...": "..."
    },
    {
      "id": "msg_002",
      "booking_id": 67890,
      "content": "Can I check in early?",
      "timestamp": "2025-09-15T08:00:00Z",
      "channel": "sms",
      "sender_type": "guest",
      "...": "..."
    }
  ],
  "failed_items": [],
  "summary": {
    "total_attempted": 1,
    "succeeded": 1,
    "failed": 0,
    "success_rate": 1.0
  }
}
```

**Interpretation**:
- Partial name match finds all messages from "John Smith"
- Results span multiple bookings (12345, 67890)
- Multiple channels (email, SMS) included

### Example 1.3: Get Complete Conversation History

**Use Case**: View full conversation timeline for a booking with proper channel labels.

**MCP Tool Invocation**:
```python
get_conversation_history(booking_id=12345)
```

**Expected Response**:
```json
{
  "booking_id": 12345,
  "messages": [
    {
      "id": "msg_1",
      "booking_id": 12345,
      "content": "Booking confirmed!",
      "timestamp": "2025-10-01T12:00:00Z",
      "channel": "email",
      "sender_type": "system",
      "...": "..."
    },
    {
      "id": "msg_2",
      "booking_id": 12345,
      "content": "What time is check-in?",
      "timestamp": "2025-10-10T10:00:00Z",
      "channel": "platform",
      "sender_type": "guest",
      "...": "..."
    },
    {
      "id": "msg_3",
      "booking_id": 12345,
      "content": "Check-in is at 3 PM",
      "timestamp": "2025-10-10T12:00:00Z",
      "channel": "email",
      "sender_type": "property_manager",
      "...": "..."
    }
  ],
  "total_count": 3,
  "channels_used": ["email", "platform"]
}
```

**Interpretation**:
- Complete chronological timeline (oldest → newest)
- System message (booking confirmation) + guest/PM messages
- Multi-channel consolidation (email + Airbnb platform)

### Example 1.4: Search with Date Range Filter

**Use Case**: Find all messages from the last 7 days for reporting.

**MCP Tool Invocation**:
```python
search_messages(
    start_date="2025-10-06",
    end_date="2025-10-13",
    limit=100
)
```

**Expected Response**:
```json
{
  "successful_results": [
    // Messages from last 7 days, ordered by timestamp
  ],
  "failed_items": [],
  "summary": {
    "total_attempted": 1,
    "succeeded": 1,
    "failed": 0,
    "success_rate": 1.0
  }
}
```

---

## Feature 2: Partial Failure Handling

### Example 2.1: Batch Property Retrieval with Partial Failures

**Use Case**: Retrieve multiple properties where some IDs may be invalid.

**MCP Tool Invocation**:
```python
batch_get_properties(property_ids=[101, 102, 999, 104])
```

**Expected Response**:
```json
{
  "successful_results": [
    {
      "id": 101,
      "name": "Beach House A",
      "city": "Miami",
      "...": "..."
    },
    {
      "id": 102,
      "name": "Mountain Cabin B",
      "city": "Aspen",
      "...": "..."
    },
    {
      "id": 104,
      "name": "City Apartment C",
      "city": "New York",
      "...": "..."
    }
  ],
  "failed_items": [
    {
      "item_id": "999",
      "error_type": "not_found",
      "error_message": "Property with ID 999 does not exist in Hostaway",
      "remediation": "Verify the property ID exists. Use GET /api/listings to see available properties."
    }
  ],
  "summary": {
    "total_attempted": 4,
    "succeeded": 3,
    "failed": 1,
    "success_rate": 0.75
  }
}
```

**Interpretation**:
- 3 of 4 properties retrieved successfully
- Property 999 failed with clear error type (not_found)
- Actionable remediation guidance provided
- Summary metrics show 75% success rate

### Example 2.2: Batch Booking Retrieval with Rate Limit

**Use Case**: Retrieve multiple bookings where rate limit might be hit.

**MCP Tool Invocation**:
```python
batch_get_bookings(booking_ids=[201, 202, 203, 204, 205])
```

**Expected Response (with rate limit)**:
```json
{
  "successful_results": [
    {"id": 201, "...": "..."},
    {"id": 202, "...": "..."},
    {"id": 203, "...": "..."}
  ],
  "failed_items": [
    {
      "item_id": "204",
      "error_type": "rate_limit",
      "error_message": "Rate limit exceeded: 20 req/10s",
      "remediation": "Retry after 5 seconds or reduce request rate. Current limit: 20 req/10s."
    },
    {
      "item_id": "205",
      "error_type": "rate_limit",
      "error_message": "Rate limit exceeded: 20 req/10s",
      "remediation": "Retry after 5 seconds or reduce request rate. Current limit: 20 req/10s."
    }
  ],
  "summary": {
    "total_attempted": 5,
    "succeeded": 3,
    "failed": 2,
    "success_rate": 0.6
  }
}
```

**Interpretation**:
- First 3 bookings retrieved successfully
- Bookings 204, 205 hit rate limit (20 req/10s)
- Remediation provides retry guidance (wait 5 seconds)
- Partial success: 60% success rate

### Example 2.3: Handling Multiple Error Types

**Use Case**: Batch operation encountering different failure types.

**MCP Tool Invocation**:
```python
batch_get_properties(property_ids=[301, 302, 999, 304])
# Assume: 301 exists, 302 unauthorized, 999 not found, 304 timeout
```

**Expected Response**:
```json
{
  "successful_results": [
    {"id": 301, "...": "..."}
  ],
  "failed_items": [
    {
      "item_id": "302",
      "error_type": "unauthorized",
      "error_message": "Permission denied for property 302",
      "remediation": "Check API permissions for accessing properties. Verify API key has required scopes."
    },
    {
      "item_id": "999",
      "error_type": "not_found",
      "error_message": "Property 999 not found",
      "remediation": "Verify property ID exists in Hostaway"
    },
    {
      "item_id": "304",
      "error_type": "timeout",
      "error_message": "Upstream service timeout for property 304",
      "remediation": "Retry with exponential backoff."
    }
  ],
  "summary": {
    "total_attempted": 4,
    "succeeded": 1,
    "failed": 3,
    "success_rate": 0.25
  }
}
```

**Interpretation**:
- Only 1 of 4 succeeded (25% success rate)
- Failed items categorized by error type: unauthorized, not_found, timeout
- Each error type has specific remediation guidance
- Client can filter/handle errors by type (retry timeouts, fix auth for unauthorized, skip not_found)

---

## Feature 3: Edge Cases & Error Handling

### Example 3.1: Empty Results (No Messages)

**Use Case**: Search for messages on a new booking with no communication yet.

**MCP Tool Invocation**:
```python
search_messages(booking_id=99999)
```

**Expected Response**:
```json
{
  "successful_results": [],
  "failed_items": [],
  "summary": {
    "total_attempted": 1,
    "succeeded": 1,
    "failed": 0,
    "success_rate": 1.0
  }
}
```

**Interpretation**:
- Empty result set (no errors)
- Success rate 100% (empty result ≠ failure)
- Client handles gracefully: "No messages found for this booking"

### Example 3.2: Pagination for Large Result Sets

**Use Case**: Retrieve conversation with >100 messages.

**MCP Tool Invocation**:
```python
# Page 1
get_conversation_history(booking_id=12345, limit=50, offset=0)

# Page 2
get_conversation_history(booking_id=12345, limit=50, offset=50)

# Page 3
get_conversation_history(booking_id=12345, limit=50, offset=100)
```

**Expected Response (Page 1)**:
```json
{
  "booking_id": 12345,
  "messages": [
    // 50 messages (oldest)
  ],
  "total_count": 150,  // Total messages in conversation
  "channels_used": ["email", "sms", "platform"]
}
```

**Interpretation**:
- `total_count=150` indicates 3 pages needed (50 messages each)
- Client paginates using `offset` parameter
- Messages ordered chronologically across pages

### Example 3.3: Special Characters in Guest Names

**Use Case**: Search for guest with emojis or special characters in name.

**MCP Tool Invocation**:
```python
search_messages(guest_name="José García 🌟")
```

**Expected Response**:
```json
{
  "successful_results": [
    {
      "id": "msg_001",
      "content": "¡Hola! Excited for my stay!",
      "...": "..."
    }
  ],
  "failed_items": [],
  "summary": {"...": "..."}
}
```

**Interpretation**:
- UTF-8 encoding supported (accents, emojis)
- Partial match works with special characters
- No encoding errors

---

## Testing Checklist

### ✅ Message Search & History
- [ ] Search by booking ID returns all messages
- [ ] Search by guest name (partial match) works
- [ ] Date range filtering returns correct subset
- [ ] Channel filtering excludes unwanted channels
- [ ] Pagination works for >100 messages
- [ ] Empty results handled gracefully
- [ ] Multi-channel consolidation chronological

### ✅ Partial Failure Handling
- [ ] Batch operation with all successes (100% rate)
- [ ] Batch operation with partial failures (50-90% rate)
- [ ] Batch operation with all failures (0% rate)
- [ ] Error types correctly categorized (not_found, unauthorized, rate_limit, timeout)
- [ ] Remediation guidance actionable
- [ ] Summary metrics accurate (total, succeeded, failed, rate)

### ✅ Edge Cases
- [ ] Empty result sets (no errors)
- [ ] Special characters (UTF-8, emojis)
- [ ] Pagination limits (0, 1, 1000, 1001)
- [ ] Concurrent requests (no race conditions)
- [ ] Rate limit behavior (retry guidance)

---

## Troubleshooting

### Issue: 401 Unauthorized

**Symptom**: All requests return `{"detail": "Missing API key"}`

**Solution**:
1. Verify `REMOTE_MCP_API_KEY` set in Claude Desktop config
2. Check API key matches `.env` on VPS
3. Restart Claude Desktop after config change

```bash
# Verify API key on VPS
ssh root@72.60.233.157 'grep MCP_API_KEY /opt/hostaway-mcp/.env'
```

### Issue: Empty Message Results

**Symptom**: `search_messages()` returns empty `successful_results`

**Possible Causes**:
1. **No messages exist**: Booking has no communication history (expected behavior)
2. **Invalid booking_id**: Booking doesn't exist (should show in failed_items)
3. **Date range too narrow**: Messages outside filter range

**Solution**:
```python
# Widen date range
search_messages(
    booking_id=12345,
    start_date="2025-01-01",  # Expand range
    end_date="2025-12-31"
)

# Remove all filters
get_conversation_history(booking_id=12345)  # Get all messages
```

### Issue: Partial Failure Rate Too High

**Symptom**: `success_rate < 0.5` (more failures than successes)

**Solution**:
1. Check `failed_items` for error patterns
2. If mostly `rate_limit`: Reduce batch size or add delays
3. If mostly `not_found`: Validate IDs before batch operation
4. If mostly `timeout`: Increase timeout or retry with smaller batches

```python
# Reduce batch size to avoid rate limits
batch_get_properties(property_ids=[101, 102, 103])  # 3 at a time instead of 50
```

---

## Next Steps

1. **Explore MCP Tools**: Use Claude Desktop to invoke `search_messages` and `get_conversation_history`
2. **Test Edge Cases**: Try empty results, special characters, large result sets
3. **Monitor Metrics**: Track `success_rate` in batch operations
4. **Review Logs**: Check audit logs for message access (privacy compliance)
5. **Implement v1.2**: Message sending, real-time notifications (future release)

---

**Quickstart Complete** | v1.1 Features Ready for Use
