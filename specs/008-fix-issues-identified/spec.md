# Feature Specification: MCP Server Issues Resolution

**Feature Branch**: `008-fix-issues-identified`
**Created**: 2025-10-28
**Status**: Draft
**Input**: User description: "Fix issues identified in MCP server test report"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Distinguish Between Authentication Failures and Missing Routes (Priority: P1)

As an API consumer, when I make a request to a non-existent endpoint, I need to receive a 404 Not Found response instead of a 401 Unauthorized response, so I can quickly distinguish between authentication issues and incorrect API usage.

**Why this priority**: This is a fundamental REST API convention that directly impacts developer experience. Without proper 404 responses, developers waste time debugging authentication when the real issue is using the wrong endpoint. This affects all API consumers and creates confusion in error logs.

**Independent Test**: Can be fully tested by making requests to non-existent routes (e.g., `/api/nonexistent`) both with and without authentication headers, and verifying that 404 is returned before authentication is checked.

**Acceptance Scenarios**:

1. **Given** a request to a non-existent endpoint `/api/nonexistent` with no authentication header, **When** the request is processed, **Then** the system returns 404 Not Found with message "Route not found"
2. **Given** a request to a non-existent endpoint `/api/fake-route` with valid authentication, **When** the request is processed, **Then** the system returns 404 Not Found (not 200 or 401)
3. **Given** a request to an existing endpoint `/api/listings` with no authentication, **When** the request is processed, **Then** the system returns 401 Unauthorized
4. **Given** a request to an existing endpoint with invalid authentication, **When** the request is processed, **Then** the system returns 401 Unauthorized

---

### User Story 2 - Monitor Rate Limit Status (Priority: P2)

As an API consumer, I need to see rate limit information in response headers, so I can proactively manage my request rate and avoid being throttled.

**Why this priority**: Rate limit transparency is an industry-standard practice that prevents unexpected throttling and improves API consumer experience. Without visible rate limits, consumers have no way to know when they're approaching limits, leading to failed requests and poor user experience.

**Independent Test**: Can be fully tested by making authenticated API requests and inspecting response headers for `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` values that accurately reflect the current state.

**Acceptance Scenarios**:

1. **Given** an authenticated request to any protected endpoint, **When** the response is received, **Then** headers include `X-RateLimit-Limit: 15` (for IP-based) or `20` (for account-based)
2. **Given** multiple consecutive requests from the same IP, **When** each response is received, **Then** `X-RateLimit-Remaining` decrements correctly
3. **Given** a rate limit bucket that will reset at a specific time, **When** a response is received, **Then** `X-RateLimit-Reset` contains the Unix timestamp of the reset time
4. **Given** a request that exceeds the rate limit, **When** the 429 response is received, **Then** all three rate limit headers are present with accurate values

---

### User Story 3 - Generate Test API Keys Easily (Priority: P3)

As a developer setting up the MCP server locally, I need a documented way to generate test API keys, so I can test MCP endpoints without needing access to the production database.

**Why this priority**: This is a developer experience improvement that primarily affects local development and testing. While important for productivity, it doesn't block production functionality. The workaround (direct database access) is available but cumbersome.

**Independent Test**: Can be fully tested by following the documentation to generate a test API key, then using that key to make authenticated requests that succeed.

**Acceptance Scenarios**:

1. **Given** a local development environment with Supabase running, **When** a developer runs the key generation script, **Then** a valid API key in format `mcp_{base64_token}` is generated
2. **Given** a generated test API key, **When** the key is used in the `X-API-Key` header, **Then** authenticated endpoints respond successfully (not 401)
3. **Given** the key generation documentation, **When** a new developer follows the steps, **Then** they can generate and use a test key in under 5 minutes
4. **Given** a generated test key in the database, **When** viewing the `api_keys` table, **Then** the key_hash is properly stored with SHA-256 hashing

---

### Edge Cases

- What happens when a request matches a route pattern but uses an unsupported HTTP method (e.g., DELETE /health)? Should return 405 Method Not Allowed, not 401.
- How does the system handle rate limit edge cases like simultaneous requests that arrive at exactly the rate limit boundary?
- What happens when a user tries to generate an API key without proper database permissions?
- How does the rate limit reset work across server restarts? Should rate limit state be persisted or reset on restart?
- What happens when rate limit headers cannot be calculated (e.g., during system errors)? Should they be omitted or return default values?

## Requirements *(mandatory)*

### Functional Requirements

#### Issue 1: 404 vs 401 Priority

- **FR-001**: System MUST return HTTP 404 Not Found for requests to non-existent routes, regardless of authentication status
- **FR-002**: System MUST only return HTTP 401 Unauthorized when a request to an existing, protected route lacks valid authentication
- **FR-003**: System MUST check route existence before checking authentication credentials
- **FR-004**: Error messages for 404 responses MUST clearly indicate the route was not found (e.g., "Route '/api/nonexistent' not found")
- **FR-005**: Error messages for 401 responses MUST clearly indicate the authentication issue (e.g., "Missing API key" or "Invalid API key")

#### Issue 2: Rate Limit Headers

- **FR-006**: System MUST include `X-RateLimit-Limit` header in all responses to protected endpoints, indicating the maximum requests allowed in the time window
- **FR-007**: System MUST include `X-RateLimit-Remaining` header showing the number of requests remaining in the current time window
- **FR-008**: System MUST include `X-RateLimit-Reset` header containing the Unix timestamp when the rate limit window resets
- **FR-009**: Rate limit headers MUST reflect the applicable limit type (IP-based at 15 req/10s or account-based at 20 req/10s)
- **FR-010**: System MUST include rate limit headers in 429 Too Many Requests responses with accurate remaining count (0) and reset time

#### Issue 3: Test API Key Generation

- **FR-011**: System MUST provide a documented script or CLI command to generate test API keys for local development
- **FR-012**: Generated API keys MUST follow the format `mcp_{base64_urlsafe_token}` with at least 32 characters of entropy
- **FR-013**: Key generation process MUST create the corresponding SHA-256 hash for storage in the database
- **FR-014**: Key generation documentation MUST include step-by-step instructions for both local Supabase and remote VPS setups
- **FR-015**: Generated test keys MUST be associated with a test organization and include required fields (organization_id, created_by_user_id, is_active=true)

### Key Entities *(include if feature involves data)*

- **Rate Limit State**: Tracks request counts per IP address or organization ID, time window boundaries, and reset timestamps. Maintained in-memory for performance.
- **API Key**: Authentication credential with format `mcp_{base64_token}`, stored as SHA-256 hash in database, associated with organization_id and user_id.
- **Route Registry**: Collection of all valid API routes used to distinguish between non-existent routes (404) and existing routes requiring authentication (401).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can distinguish between authentication failures and route errors by receiving correct HTTP status codes (404 for missing routes, 401 for auth issues) in 100% of test cases
- **SC-002**: API consumers can monitor their rate limit status by inspecting response headers, with rate limit information present in 100% of responses to protected endpoints
- **SC-003**: New developers can generate and use test API keys for local development in under 5 minutes following documentation
- **SC-004**: Rate limit headers accurately reflect current state with zero false positives or negatives in automated tests
- **SC-005**: System response times remain under 500ms after implementing middleware changes, maintaining current performance levels

## Assumptions *(optional)*

1. **Rate Limit Storage**: Rate limit state is maintained in-memory and resets on server restart. For distributed deployments, a shared state store would be needed but is out of scope.

2. **Middleware Order**: Adjusting middleware order to check routes before authentication won't negatively impact security or performance. Public routes will still bypass authentication.

3. **Header Overhead**: Adding three headers to every response has negligible performance impact given modern HTTP/2 compression.

4. **Key Generation Security**: Test API keys generated for local development should use the same security standards (SHA-256 hashing, proper entropy) as production keys.

5. **Database Schema**: The existing `api_keys` table schema supports all required fields (organization_id, key_hash, created_by_user_id, is_active, created_at) without modifications.

6. **Backwards Compatibility**: Changes to middleware order and header additions won't break existing API consumers, as they're additive (new headers) or fixes (correct status codes).

## Out of Scope *(optional)*

- Distributed rate limiting across multiple server instances (requires shared state store)
- Rate limit customization per organization or API key (all keys use the same limits)
- Graphical user interface for API key management (CLI/script only)
- Key rotation mechanisms or expiration policies (manual key management only)
- Retry-After header calculations for 429 responses (basic rate limit headers only)
- Persistent rate limit state across server restarts
- Advanced rate limiting algorithms (token bucket with burst capacity, sliding window)

## Dependencies *(optional)*

- **Supabase**: Required for API key storage and retrieval. Local development requires Supabase Docker setup.
- **FastAPI Middleware System**: Changes depend on FastAPI's middleware execution order and exception handling mechanisms.
- **Existing Authentication Flow**: Rate limit headers depend on successful authentication to identify the organization context.
- **Test Infrastructure**: API key generation testing requires access to Supabase database (local or remote).

## Open Questions *(optional)*

None - all requirements are clear and testable based on the test report findings.
