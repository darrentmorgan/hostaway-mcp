# Feature Specification: MCP Server Context Window Protection

**Feature Branch**: `005-project-brownfield-hardening`
**Created**: 2025-10-15
**Status**: Draft
**Input**: User description: "Project: Brownfield hardening of an existing MCP server used by Claude. Context & Problem: We have an existing MCP server integrated with Claude; large tool/resource outputs are overrunning the model's context window, degrading quality and causing truncation or hard errors..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Paginated List Results (Priority: P1)

Claude requests a list of resources (e.g., listings, bookings, transactions) from the MCP server and receives a manageable first page of results with clear instructions on how to fetch additional pages if needed.

**Why this priority**: This addresses the most common cause of context overflow - unbounded list operations. Without pagination, a single tool call can return hundreds or thousands of items, immediately consuming the entire context window. This is the foundation for all other improvements.

**Independent Test**: Can be fully tested by calling any list endpoint with a large dataset and verifying it returns only a limited number of items plus pagination metadata, delivering immediate value by preventing context overflow on the most common operations.

**Acceptance Scenarios**:

1. **Given** Claude requests a list of 500 bookings, **When** the server processes the request, **Then** the response contains the first 50 bookings, total count of 500, and a cursor for fetching the next page
2. **Given** Claude uses a pagination cursor from a previous response, **When** requesting the next page, **Then** the server returns the next batch of items with an updated cursor
3. **Given** Claude requests a list with only 10 total items, **When** the server processes the request, **Then** all items are returned without pagination metadata (no unnecessary overhead for small datasets)
4. **Given** Claude reaches the final page of results, **When** processing the response, **Then** no next cursor is provided, indicating completion

---

### User Story 2 - Automatic Response Summarization (Priority: P1)

When Claude requests data that would exceed safe token limits, the server automatically provides a condensed summary with key information and instructions for accessing complete details on demand.

**Why this priority**: Even with pagination, individual items can be verbose (e.g., a booking with extensive guest details, property amenities, pricing breakdowns). Summarization prevents single-item bloat while keeping the most important information accessible. This complements pagination by handling per-item verbosity.

**Independent Test**: Can be fully tested by requesting a resource with extensive details and verifying the response contains only essential fields with instructions for accessing full details, delivering value by preventing single-item context overflow.

**Acceptance Scenarios**:

1. **Given** Claude requests booking details that exceed 2000 tokens when fully expanded, **When** the server processes the request, **Then** a summary with essential fields (ID, status, guest name, dates, property) is returned with instructions to request specific detail categories
2. **Given** Claude requests full financial details after receiving a summary, **When** the server processes the detailed request, **Then** only the financial section is returned in full detail
3. **Given** Claude requests a small resource under 500 tokens, **When** the server processes the request, **Then** full details are returned without summarization (no unnecessary complexity for small responses)
4. **Given** a summary response includes token budget information, **When** Claude processes the response, **Then** the metadata shows estimated tokens used and available budget remaining

---

### User Story 3 - Configurable Token Budgets (Priority: P2)

Operations teams can configure token limits and response behaviors through environment variables or configuration files without code changes, allowing tailored limits for different deployment environments or use cases.

**Why this priority**: Different environments and workflows have different needs. Development may need larger limits for debugging, while production prioritizes strict controls. This enables the same codebase to serve multiple use cases safely.

**Independent Test**: Can be fully tested by modifying configuration values and verifying the server respects new limits without restart, delivering value by allowing runtime adaptation to different operational requirements.

**Acceptance Scenarios**:

1. **Given** an operations engineer updates the token limit configuration from 4000 to 8000 tokens, **When** the configuration is reloaded, **Then** subsequent responses respect the new 8000 token limit
2. **Given** a feature flag enables pagination for a specific endpoint, **When** that endpoint is called, **Then** pagination is applied while other endpoints remain unchanged
3. **Given** default configuration values are documented, **When** a new deployment uses defaults, **Then** safe production limits (4000 tokens per response, 50 items per page) are automatically applied
4. **Given** invalid configuration is provided, **When** the server attempts to reload, **Then** current configuration remains active and an error is logged

---

### User Story 4 - Response Chunking for Large Content (Priority: P2)

When Claude requests large text content (logs, descriptions, documents), the server intelligently chunks the content into digestible pieces with semantic boundaries, allowing progressive reading without overwhelming the context.

**Why this priority**: Some content is inherently large (multi-page descriptions, extensive logs) but cannot be meaningfully summarized. Chunking provides a way to access this content progressively while respecting context limits.

**Independent Test**: Can be fully tested by requesting a 50KB log file and verifying it's returned in appropriately sized chunks with continuation cursors, delivering value by making large content accessible without context overflow.

**Acceptance Scenarios**:

1. **Given** Claude requests a log file with 10,000 lines, **When** the server processes the request, **Then** the first 200 lines are returned with a cursor for the next chunk and total line count
2. **Given** the server chunks content at semantic boundaries (log entry completion, paragraph breaks), **When** returning chunks, **Then** no chunks split mid-sentence or mid-entry
3. **Given** Claude requests a specific line range in a large file, **When** the server processes the request, **Then** only the requested range is returned efficiently
4. **Given** content is under 1000 tokens, **When** the server processes the request, **Then** the full content is returned without chunking

---

### User Story 5 - Telemetry and Monitoring (Priority: P3)

Engineers can observe token usage patterns, pagination adoption, and context overflow attempts through dashboards and logs, enabling data-driven optimization and early detection of issues.

**Why this priority**: While not directly user-facing, observability enables continuous improvement and proactive issue detection. This builds on the foundation of pagination and summarization by providing insights into their effectiveness.

**Independent Test**: Can be fully tested by making various API calls and verifying metrics are accurately captured and queryable, delivering value by enabling operational visibility into context management.

**Acceptance Scenarios**:

1. **Given** the server processes 100 requests, **When** reviewing metrics, **Then** each request records estimated tokens, actual bytes, item count, and processing latency
2. **Given** a request exceeds the token budget and triggers summarization, **When** the event is logged, **Then** the log includes original size, summarized size, and reduction percentage
3. **Given** pagination is used on a request, **When** viewing metrics, **Then** pagination usage is tracked separately from non-paginated requests
4. **Given** operations team sets up alerts, **When** oversized response attempts exceed 5% of traffic, **Then** an alert is triggered for investigation

---

### Edge Cases

- What happens when a cursor becomes invalid (data changed, expired)? → Server returns clear error indicating cursor invalidity and suggests re-querying from the start
- How does the system handle malformed pagination parameters? → Server validates parameters and returns descriptive errors (e.g., "invalid cursor format", "limit exceeds maximum of 200")
- What if token estimation is significantly wrong (estimates 1000, actual 5000)? → Server monitors estimation accuracy and logs large discrepancies for model tuning; falls back to hard byte limits as safety net
- How does summarization handle data types with no clear summary format (binary, complex nested objects)? → Server uses field projection (select subset of fields) rather than summarization; provides metadata about available fields
- What happens when multiple pages are requested in rapid succession? → Server caches pagination state temporarily (10 minutes) to ensure consistency even as underlying data changes
- How does chunking handle real-time streaming data? → Server snapshots data at request time for consistent pagination; real-time updates require new query

## Requirements *(mandatory)*

### Functional Requirements

#### Pagination

- **FR-001**: System MUST support cursor-based pagination on all list/search endpoints that can return more than 50 items
- **FR-002**: System MUST accept an optional `limit` parameter (default: 50, maximum: 200) specifying items per page
- **FR-003**: System MUST accept an optional `cursor` parameter (opaque string) for fetching subsequent pages
- **FR-004**: Paginated responses MUST include `nextCursor` field when additional pages exist, omitted on final page
- **FR-005**: Paginated responses MUST include `totalCount` field showing total items available across all pages
- **FR-006**: System MUST return items in consistent order within pagination sequence (sorted by creation time descending by default)
- **FR-007**: Pagination cursors MUST remain valid for at least 10 minutes after issuance
- **FR-008**: System MUST return descriptive error when cursor is invalid or expired

#### Token Budget Management

- **FR-009**: System MUST estimate token count for response payloads before sending
- **FR-010**: System MUST switch to summarization mode when estimated response exceeds configured token threshold (default: 4000 tokens)
- **FR-011**: Summarized responses MUST include instructions for fetching detailed sections on demand
- **FR-012**: System MUST include token budget metadata in responses: `estimatedTokens`, `budgetUsed`, `budgetRemaining`
- **FR-013**: Token estimation MUST use character-based approximation (1 token ≈ 4 characters) with 20% safety margin
- **FR-014**: System MUST log actual vs estimated token counts for accuracy monitoring

#### Summarization and Compression

- **FR-015**: System MUST provide condensed field sets for verbose data structures (bookings, listings, financial records)
- **FR-016**: Summaries MUST retain all identifying fields (IDs, names, primary status) while compressing verbose details
- **FR-017**: System MUST support field projection via `fields` parameter allowing selective retrieval (e.g., `fields=id,status,total`)
- **FR-018**: Long text fields (descriptions, notes) MUST be truncated in summaries with character count and continuation instructions
- **FR-019**: System MUST strip redundant metadata from tool responses (verbose schemas, debug info) in production mode

#### Content Chunking

- **FR-020**: System MUST chunk large text content (logs, documents) when exceeding 2000 tokens
- **FR-021**: Chunks MUST respect semantic boundaries (complete log entries, paragraph breaks, sentence completion)
- **FR-022**: Chunked responses MUST include chunk position metadata: `chunkIndex`, `totalChunks`, `nextCursor`
- **FR-023**: System MUST support range-based requests for large content (e.g., `startLine=100&endLine=200`)

#### Configuration

- **FR-024**: System MUST read configuration from environment variables with documented defaults
- **FR-025**: System MUST support configuration file (YAML/JSON) for complex settings
- **FR-026**: System MUST allow runtime configuration reload without server restart
- **FR-027**: Configuration MUST include: `defaultPageSize`, `maxPageSize`, `tokenBudgetThreshold`, `chunkSize`, feature flags per endpoint
- **FR-028**: Invalid configuration MUST be rejected with clear error messages, falling back to previous valid config

#### Telemetry

- **FR-029**: System MUST record per-request metrics: `estimatedTokens`, `responseBytes`, `itemCount`, `latency`, `paginationUsed`, `summarizationUsed`
- **FR-030**: System MUST log oversized response attempts (exceeded budget before summarization) with original and final sizes
- **FR-031**: Metrics MUST be queryable by endpoint, time range, and outcome (paginated/summarized/chunked)
- **FR-032**: System MUST expose health endpoint reporting pagination adoption rate and average response size

#### Compatibility

- **FR-033**: All new fields (pagination metadata, token budgets) MUST be additive to existing response structures
- **FR-034**: Existing clients not using pagination MUST continue receiving first page by default (backwards compatible)
- **FR-035**: Feature flags MUST allow gradual rollout per endpoint without affecting other endpoints
- **FR-036**: System MUST support A/B testing mode where responses can be compared with/without hardening features

### Key Entities

- **PaginationCursor**: Opaque token encoding position in result set, valid for 10 minutes, includes snapshot timestamp and ordering context
- **TokenBudget**: Configuration and runtime tracking of token limits per response, includes threshold, estimation method, and actual usage
- **ResponseSummary**: Condensed representation of verbose data with essential fields retained and instructions for accessing detailed sections
- **ContentChunk**: Segment of large text content with semantic boundaries, position metadata, and continuation cursor
- **TelemetryRecord**: Per-request metrics capturing token usage, response characteristics, and optimization strategies applied

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Claude workflows complete multi-step tasks without context overflow errors in 99.9% of sessions (currently ~60% due to overflows)
- **SC-002**: Average token usage per tool response reduces by 60% or more (from ~6000 tokens to ~2400 tokens)
- **SC-003**: 95% of list endpoints use pagination within 2 weeks of deployment
- **SC-004**: Support tickets related to "truncated responses" or "context errors" decrease by 80% within 1 month
- **SC-005**: Response time increases by no more than 10% (p95 latency) due to token estimation and summarization overhead
- **SC-006**: Engineers can diagnose context issues using telemetry dashboards within 5 minutes (vs 30+ minutes currently)
- **SC-007**: Users successfully navigate paginated results in 95% of attempts without confusion or errors
- **SC-008**: Token estimation accuracy within 20% of actual usage for 90% of responses

## Assumptions *(mandatory)*

- Current MCP server uses JSON for request/response serialization
- Claude Desktop is the primary client and supports opaque pagination cursors
- Server has access to response payload before sending (can intercept and analyze)
- Token estimation can use simple character-based heuristics (4 chars/token) with acceptable accuracy
- Most data access patterns are read-heavy (lists, searches, reads) vs write-heavy
- Pagination cursors stored in memory (Redis/similar) for 10-minute TTL acceptable
- Existing endpoints return predictable JSON structures amenable to field projection
- Operations team can deploy configuration changes independently of code deployments
- Telemetry can be stored in time-series database or log aggregation system
- Backwards compatibility requirement applies to external clients only (internal tools can adapt immediately)

## Dependencies *(include if applicable)*

- Token estimation library or service capable of approximating Claude token counts from text
- Configuration management system supporting hot-reload (e.g., file watchers, environment variable updates)
- Metrics collection infrastructure (e.g., Prometheus, StatsD, CloudWatch)
- Pagination cursor storage with TTL support (e.g., Redis, in-memory cache)
- Existing MCP server framework extensible via middleware or interceptors

## Open Questions *(include if blocking issues exist)*

None - all critical decisions have reasonable defaults documented in Requirements and Assumptions sections.

## Non-Functional Requirements *(include if applicable)*

### Performance

- Pagination overhead MUST NOT exceed 50ms per request (cursor lookup, state management)
- Token estimation MUST complete within 20ms for responses up to 100KB
- Configuration reload MUST complete within 100ms without dropping in-flight requests
- Metric recording MUST NOT add more than 10ms latency to request processing

### Reliability

- Pagination cursor expiration MUST handle gracefully with clear user guidance (re-query instructions)
- Token estimation failures MUST fall back to byte-based limits (safe default) rather than failing requests
- Configuration errors MUST NOT crash server or drop traffic (fail-safe to previous config)
- Telemetry failures MUST NOT affect request success (fire-and-forget metric recording)

### Security

- Pagination cursors MUST NOT expose internal data structure or query details (opaque, signed)
- Token budget metadata MUST NOT leak sensitive information about server internals
- Configuration changes MUST be validated before application (schema validation, range checks)

### Observability

- All pagination, summarization, and chunking decisions MUST be logged at INFO level
- Token estimation accuracy MUST be sampled (1% of requests) and reported to metrics
- Configuration changes MUST be logged with old/new values and timestamp
- Oversized response attempts MUST trigger alerts when exceeding 5% of traffic

## Risks & Mitigations

### Risk 1: Hidden Client Dependencies on Unbounded Payloads

**Likelihood**: Medium | **Impact**: High

**Description**: External clients may rely on receiving complete datasets in single responses (e.g., automated scripts expecting all 1000 listings at once).

**Mitigation**:
- Feature flags per endpoint for gradual rollout
- Default page size starts at 200 items (higher than typical) for soft landing
- Backwards compatibility: clients not using pagination still get first page
- Contract tests validate no breaking changes to response schemas
- Canary deployment: 5% → 25% → 50% → 100% over 2 weeks with rollback capability

### Risk 2: Pagination Increases Round-trips

**Likelihood**: High | **Impact**: Medium

**Description**: Multi-page workflows require multiple API calls, potentially slowing down Claude's analysis.

**Mitigation**:
- Intelligent default page size (50 items) balances single-page and multi-page scenarios
- Server-side prefetch for common patterns (e.g., "next page" cursor pre-generated)
- Batch operations where possible (e.g., "get pages 1-3" in single call)
- Telemetry identifies endpoints with excessive pagination and allows tuning

### Risk 3: Token Estimation Inaccuracy

**Likelihood**: Medium | **Impact**: Medium

**Description**: Character-based token estimation may be significantly wrong for certain content types (code, special characters, non-English text).

**Mitigation**:
- 20% safety margin built into estimation
- Continuous monitoring of estimation vs actual with model retraining
- Hard byte limits as secondary safety (10KB regardless of token estimate)
- Sampling mode for accuracy testing (1% of responses validated against actual tokenizer)

### Risk 4: Configuration Errors

**Likelihood**: Low | **Impact**: High

**Description**: Invalid configuration could break pagination, disable summarization, or cause cascading failures.

**Mitigation**:
- Schema validation for all configuration values before application
- Fail-safe defaults: invalid config reverts to previous known-good state
- Configuration changes logged and audited
- Dry-run mode for testing configuration before applying to production

## Out of Scope

- Changing MCP protocol or transport mechanism
- Client-side UI changes (beyond what Claude Desktop already supports)
- Complete server rewrite or framework migration
- Real-time streaming response handling (deferred to future iteration)
- Multi-tenant cursor sharing or cross-organization pagination
- GraphQL or alternative query language support
- Binary/media content chunking (focus on text/JSON initially)
