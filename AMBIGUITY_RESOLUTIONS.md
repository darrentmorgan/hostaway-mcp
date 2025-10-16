# Ambiguity Resolutions - Specification Clarifications

**Date**: 2025-10-12
**Feature**: Hostaway MCP Server with Authentication
**Purpose**: Resolve ambiguous terms identified in production readiness review

---

## Resolved Ambiguities

### 1. "User Context" in Audit Logging (FR-012, CHK113)

**Original Ambiguous Requirement**:
> "System MUST log all AI tool invocations with user context for audit purposes" - FR-012

**Ambiguity**: What constitutes "user context"?

**Resolution**: "User context" is defined as the following data points logged for each MCP tool invocation:

**Mandatory Fields**:
- `correlation_id` (UUID) - Request tracing identifier
- `timestamp` (ISO 8601) - Exact invocation time
- `tool_name` (string) - MCP tool/endpoint invoked
- `client_ip` (IP address) - Source IP of the request
- `http_method` (string) - HTTP verb (GET, POST, etc.)
- `request_path` (string) - Full API endpoint path

**Optional Fields** (when available):
- `user_agent` (string) - Client user agent string
- `mcp_session_id` (string) - MCP session identifier
- `authentication_status` (boolean) - Whether request was authenticated
- `response_status` (integer) - HTTP status code returned
- `response_time_ms` (integer) - Request processing time

**Example Log Entry**:
```json
{
  "timestamp": "2025-10-12T15:30:45.123Z",
  "level": "INFO",
  "correlation_id": "9fa246ea-4191-4bbd-a9da-5e3680c4d387",
  "tool_name": "list_properties",
  "client_ip": "192.168.1.100",
  "http_method": "GET",
  "request_path": "/api/listings?limit=10",
  "user_agent": "Claude-Desktop/1.0",
  "response_status": 200,
  "response_time_ms": 250
}
```

**Updated Requirement** (FR-012):
> "System MUST log all AI tool invocations with user context (correlation_id, timestamp, tool_name, client_ip, http_method, request_path) for audit purposes"

**Traceability**: Resolves CHK113, implements Spec §FR-012, aligns with Constitution §III (Security by Default)

---

### 2. "Routine Guest Communication" in Success Criteria (SC-006, CHK112)

**Original Ambiguous Requirement**:
> "Property managers can delegate 80% of routine guest communication to AI without manual review" - SC-006

**Ambiguity**: What qualifies as "routine" vs requiring manual review?

**Resolution**: "Routine guest communication" is defined as the following message types:

**Routine Messages** (AI-delegated, no manual review):
1. **Pre-Arrival Messages**:
   - Check-in instructions (time, location, access codes)
   - Property directions and parking information
   - WiFi credentials and amenity details
   - Local area recommendations

2. **During-Stay Messages**:
   - Automated welcome messages
   - Scheduled check-out reminders
   - FAQ responses (amenities, appliances, local services)
   - Standard maintenance appointment notifications

3. **Post-Stay Messages**:
   - Thank you and review request messages
   - Feedback collection
   - Loyalty program information

**Non-Routine Messages** (REQUIRE manual review):
1. **Incident Response**:
   - Guest complaints or disputes
   - Emergency situations (safety, security)
   - Damage reports or claims
   - Refund or compensation requests

2. **Policy Exceptions**:
   - Special accommodation requests
   - Booking modifications or cancellations
   - Early check-in / late check-out approval
   - Pet policy exceptions

3. **Financial Matters**:
   - Payment disputes
   - Extra charges or fees
   - Deposit or security issues

4. **Legal/Compliance**:
   - Guest behavior violations
   - Regulatory compliance matters
   - Privacy or data requests

**Measurement Method**:
- Track total guest messages sent per month
- Categorize each as "routine" (AI) or "non-routine" (manual)
- Calculate percentage: `(routine_messages / total_messages) * 100`
- **Success = ≥80% routine messages handled by AI**

**Updated Requirement** (SC-006):
> "Property managers can delegate 80% of routine guest communication (pre-arrival instructions, during-stay FAQs, post-stay thank-yous) to AI without manual review, excluding incident response, policy exceptions, financial matters, and legal/compliance issues"

**Traceability**: Resolves CHK112, clarifies Spec §SC-006

---

### 3. "Property" vs "Listing" Terminology Standardization (CHK109)

**Original Inconsistency**:
- Spec uses "Property" (§User Stories, §Key Entities)
- Plan/Tasks use "Listing" (API endpoints, file names)
- Data model uses both interchangeably

**Resolution**: Standardize on **"Listing"** as the primary term:

**Rationale**:
1. Aligns with Hostaway API terminology (`GET /listings`)
2. Matches implemented code structure (`src/api/routes/listings.py`, `src/models/listings.py`)
3. Consistent with MCP tool naming (`list_properties` → maps to `/listings` endpoint)

**Terminology Mapping**:
- **Primary**: "Listing" (use in code, API, technical docs)
- **Alias**: "Property" (acceptable in user-facing descriptions, business context)
- **Avoid**: Mixing terms in same document section

**Updated Usage**:
- API endpoints: `/api/listings` ✅
- Code/models: `Listing`, `ListingSummary`, `get_listing_by_id()` ✅
- User stories: "Property listing details" ✅ (natural language)
- Data model: `Listing` entity ✅

**Traceability**: Resolves CHK109, improves Spec §Requirements consistency

---

## Implementation Status

| Ambiguity | Status | Resolution Document | Code Changes Needed |
|-----------|--------|---------------------|---------------------|
| User Context (FR-012) | ✅ Resolved | This document | None (already implemented in logging.py) |
| Routine Communication (SC-006) | ✅ Resolved | This document | None (measurement criteria defined) |
| Property/Listing Terminology | ✅ Resolved | This document | None (code already uses "Listing") |

---

## Validation

**How to Verify Resolutions**:

1. **User Context Logging**:
   ```bash
   # Check logs for required fields
   docker compose logs hostaway-mcp | jq 'select(.correlation_id != null)'
   ```

2. **Routine Communication Tracking**:
   ```bash
   # Measure routine vs non-routine ratio (when US4 implemented)
   # Calculate from message logs categorized by type
   ```

3. **Terminology Consistency**:
   ```bash
   # Verify "Listing" usage in code
   grep -r "class.*Listing" src/models/
   grep -r "get_listing" src/services/
   ```

---

**Status**: ✅ **ALL AMBIGUITIES RESOLVED**
**Next Action**: Update spec.md with clarified definitions (optional - already implemented correctly)
