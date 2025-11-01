# Feature Specification: API-Level Response Summarization

**Feature Branch**: `009-add-api-level`
**Created**: 2025-10-29
**Status**: ✅ Complete (Deployed to Production)
**Deployed**: 2025-10-30
**PR**: #7 (merged to `001-we-need-to`)
**Input**: User description: "Add API-level response summarization to prevent context window bloat for MCP consumers. Currently only local mcp_stdio_server.py summarizes responses. Need VPS API to support optional summary=true query parameter that returns compact essential fields instead of full JSON payloads."

**Terminology Note**: In this specification, "Property" and "Listing" are used interchangeably to refer to the same entity - a vacation rental property managed through Hostaway. The API endpoints and data models use the term "Listing" (e.g., `/api/listings`, `SummarizedListing`), while user-facing descriptions may use "Property" for clarity.

## Clarifications

### Session 2025-10-29

- Q: When `summary=true` is used on a detail endpoint (e.g., `GET /api/listings/123?summary=true`), what should the system do? → A: Return full details without any warning or error message (silently ignore the parameter)
- Q: What data type and format should date fields use in summarized booking responses (checkIn, checkOut)? → A: ISO 8601 strings (YYYY-MM-DD)
- Q: Should summarized responses be cached differently than full responses (e.g., different cache TTL or cache keys)? → A: Use same caching strategy for both (same TTL, separate cache keys by full URL including query params)
- Q: What data type and format should numeric fields use in summarized responses (bedrooms, totalPrice)? → A: Integer for bedrooms, decimal/float for totalPrice
- Q: Should the API log when summary mode is used for monitoring and usage analytics? → A: Yes, log summary parameter usage at INFO level

## User Scenarios & Testing

### User Story 1 - API Consumer Requests Compact Property List (Priority: P1)

An API consumer (AI assistant, mobile app, or third-party integration) needs to display a list of properties but doesn't need full details. They request the properties endpoint with a summary flag to receive only essential information (ID, name, location, bedrooms, status) instead of complete property data including descriptions, amenities, pricing rules, and availability calendars.

**Why this priority**: This is the most common use case causing context overflow. Property listings with full details can easily exceed 50KB per property. This addresses the immediate pain point for all API consumers, especially AI assistants with limited context windows.

**Independent Test**: Can be fully tested by calling GET /api/listings?summary=true and verifying the response contains only essential fields while maintaining data accuracy. Delivers immediate value by reducing response size by 80-90%.

**Acceptance Scenarios**:

1. **Given** an API consumer wants to browse properties, **When** they request GET /api/listings?summary=true, **Then** they receive a compact response with only: property ID, name, city, country, bedrooms, and availability status
2. **Given** an API consumer doesn't specify the summary parameter, **When** they request GET /api/listings, **Then** they receive the full property details as currently implemented (backward compatible)
3. **Given** an API consumer requests 10 properties with summary=true, **When** the response is returned, **Then** the response size is under 5KB compared to 50KB+ for full details

---

### User Story 2 - API Consumer Requests Compact Booking List (Priority: P1)

An API consumer needs to display upcoming bookings but doesn't need complete guest information, payment details, or communication history. They request the bookings endpoint with a summary flag to receive only core booking information (ID, guest name, dates, property, status, price).

**Why this priority**: Booking data includes extensive nested information about guests, payments, and property details. This is equally critical as property summarization for preventing context overflow in booking-related queries.

**Independent Test**: Can be fully tested by calling GET /api/reservations?summary=true and verifying the response contains only essential booking fields. Delivers value by enabling efficient booking lists without overloading clients.

**Acceptance Scenarios**:

1. **Given** an API consumer wants to view bookings, **When** they request GET /api/reservations?summary=true, **Then** they receive a compact response with only: booking ID, guest name, check-in date, check-out date, property ID, status, and total price
2. **Given** an API consumer requests booking details, **When** they use summary=true, **Then** nested objects (guest details, property info, payment history) are excluded
3. **Given** an API consumer needs full booking details, **When** they request GET /api/reservations/{id} without summary parameter, **Then** they receive complete booking information including all nested data

---

### User Story 3 - API Consumer Gets Helpful Guidance (Priority: P2)

When an API consumer receives a summarized response, they need clear guidance on how to access full details for specific items they're interested in.

**Why this priority**: While less critical than the core functionality, this improves developer experience and reduces support requests by making the API self-documenting.

**Independent Test**: Can be tested by checking that summarized responses include a "note" field with instructions. Delivers value by reducing confusion and improving API discoverability.

**Acceptance Scenarios**:

1. **Given** an API consumer receives a summarized property list, **When** they inspect the response, **Then** they see a note field stating "Use GET /api/listings/{id} to see full property details"
2. **Given** an API consumer receives a summarized booking list, **When** they inspect the response, **Then** they see a note field stating "Use GET /api/reservations/{id} to see full booking details"

---

### Edge Cases

- What happens when summary=true is used with a details endpoint (e.g., GET /api/listings/123?summary=true)? The system silently ignores the parameter and returns full details without any warning or error message.
- How does the system handle invalid summary parameter values (e.g., summary=invalid)? Treat any truthy value (true, 1, yes) as true, otherwise default to false (full response).
- What if a summarized field is null/missing in the source data? Include the field with null value rather than omitting it to maintain consistent response schema.
- How should pagination metadata be handled in summarized responses? Include full pagination metadata (total, limit, offset) regardless of summary flag.

## Requirements

### Functional Requirements

- **FR-001**: System MUST accept a "summary" query parameter on list endpoints (/api/listings, /api/reservations)
- **FR-002**: System MUST treat summary parameter as boolean (truthy values: "true", "1", "yes" return summarized; all others return full response)
- **FR-003**: System MUST return only essential fields when summary=true:
  - Properties: id, name, city, country, bedrooms (integer), status (isActive)
  - Bookings: id, guestName, checkIn (ISO 8601 date: YYYY-MM-DD), checkOut (ISO 8601 date: YYYY-MM-DD), listingId, status, totalPrice (decimal/float)
- **FR-004**: System MUST preserve full response structure when summary parameter is absent or false (backward compatibility)
- **FR-005**: System MUST include a "note" field in summarized responses indicating how to fetch full details
- **FR-006**: System MUST maintain pagination metadata (total, limit, offset) in all responses regardless of summary flag
- **FR-007**: System MUST silently ignore summary parameter for single-item detail endpoints (GET /api/listings/{id}), returning full details without warning or error
- **FR-008**: System MUST include total item count in summarized responses to help consumers understand dataset size
- **FR-009**: Summarized responses MUST maintain the same HTTP status codes and error handling as full responses
- **FR-010**: System MUST use the same caching strategy for both summarized and full responses (same TTL, with cache keys differentiated by full URL including query parameters)
- **FR-011**: System MUST log summary parameter usage at INFO level for monitoring and usage analytics (including endpoint, user agent, and timestamp)

### Key Entities

- **Summarized Property**: Represents essential property information including unique identifier, display name, geographic location, capacity indicator (integer), and availability status
- **Summarized Booking**: Represents core booking information including unique identifier, guest identity, stay dates (ISO 8601 format: YYYY-MM-DD), associated property reference, booking state, and financial amount (decimal/float)
- **Response Metadata**: Represents pagination and guidance information including item counts, offset values, page limits, and detail retrieval instructions

## Success Criteria

### Measurable Outcomes

- **SC-001**: Summarized property list responses are 80-90% smaller than full responses for equivalent item counts
- **SC-002**: API consumers can retrieve a list of 10 properties in under 1 second with summarized responses (compared to 2-3 seconds for full responses)
- **SC-003**: All existing API functionality continues to work unchanged when summary parameter is not specified (100% backward compatibility)
- **SC-004**: AI assistants (Claude, ChatGPT) can retrieve and process 20+ properties without exceeding context window limits (validated by successful multi-property queries)
- **SC-005**: API documentation clearly explains summary parameter usage, reducing related support requests by 90%

## Assumptions

- **Assumption 1**: Consumers who need full details will make separate detail requests (GET /api/listings/{id}) rather than expecting all data in list responses
- **Assumption 2**: The existing TokenAwareMiddleware remains in place as a fallback protection mechanism even with summarization available
- **Assumption 3**: Most AI assistant queries involve browsing/filtering lists before drilling into specific items, making summary mode the ideal default behavior for these use cases
- **Assumption 4**: The essential fields chosen for summarization provide sufficient information for list/browse operations across all anticipated use cases
- **Assumption 5**: Response size reduction of 80-90% is sufficient to prevent context overflow for typical query patterns (10-20 items per request)

## Out of Scope

- Automatic detection of AI consumers vs. human consumers (all consumers use same API with explicit summary parameter)
- Custom field selection (e.g., fields=id,name,city) - only predefined essential fields available in summary mode
- Summarization of detail endpoints (GET /api/listings/{id}) - full details always returned for single-item requests
- Server-side rendering or HTML responses - API remains JSON-only
- Rate limit changes based on response size - existing rate limits apply equally to summarized and full responses
