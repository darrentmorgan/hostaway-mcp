# Implementation Plan: Guest Communication & Enhanced Error Handling (v1.1)

**Branch**: `002-enhance-the-hostaway` | **Date**: 2025-10-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/Users/darrenmorgan/AI_Projects/hostaway-mcp/specs/002-enhance-the-hostaway/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

v1.1 enhances the Hostaway MCP Server with three major capabilities:

1. **Guest Communication** - AI agents retrieve message history across all channels (email, SMS, in-app) to provide context-aware support
2. **Partial Failure Resilience** - Batch operations gracefully handle mixed success/failure scenarios without cascade failures
3. **Enhanced Test Coverage** - Increase from 72.80% to ≥80% with comprehensive edge case and error path tests

**Technical Approach**: Extend v1.0 FastAPI/MCP architecture with new Hostaway Messages API integration, implement PartialFailureResponse model for batch operations, and expand test suite focusing on boundary conditions and error paths.

## Technical Context

**Language/Version**: Python 3.12 (existing v1.0 stack)
**Primary Dependencies**: FastAPI 0.100+, fastapi-mcp 0.4+, httpx 0.27+ (async), Pydantic 2.0+, pydantic-settings
**Storage**: N/A (stateless, all data retrieved on-demand from Hostaway API)
**Testing**: pytest, pytest-asyncio, pytest-cov (target ≥80%)
**Target Platform**: Linux server (Hostinger VPS), Docker containerized
**Project Type**: Single project (API server with MCP tools)
**Performance Goals**: <2s message retrieval (100 messages), <5s batch operations (50 items), 100+ concurrent requests
**Constraints**: <500ms API response (p95), ≥80% test coverage, 99.9% uptime (excl. Hostaway API), backward compatible with v1.0
**Scale/Scope**: 3 new user stories, 18 functional requirements, 5 new entities, estimated 50-75 new tasks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: API-First Design ✅ PASS

- **Requirement**: Every feature exposed as FastAPI endpoint before MCP tool
- **Compliance**: v1.1 follows v1.0 pattern - all message retrieval and batch operations will be FastAPI endpoints first, auto-converted to MCP tools via fastapi-mcp
- **Evidence**:
  - FR-001 to FR-006 (message search) → FastAPI routes in `src/api/routes/messages.py`
  - FR-007 to FR-011 (partial failures) → Enhanced response models in existing routes
  - All endpoints will have `operation_id`, Pydantic models, docstrings, `response_model`, and tags

### Principle II: Type Safety (NON-NEGOTIABLE) ✅ PASS

- **Requirement**: Type annotations, strict validation, mypy --strict passing
- **Compliance**: All new models (Message, ConversationThread, PartialFailureResponse, BatchItem, MessageSearchCriteria) will use Pydantic with `Field` constraints
- **Evidence**:
  - All new functions will have type annotations
  - Configuration extends v1.0 `pydantic-settings` approach
  - Pre-commit hooks enforce `mypy --strict`

### Principle III: Security by Default ✅ PASS

- **Requirement**: Authentication, validation, rate limiting, audit logging, HTTPS
- **Compliance**: v1.1 reuses v1.0 security infrastructure
- **Evidence**:
  - MCP API key authentication (existing middleware)
  - Pydantic Field validation for all inputs
  - Existing rate limiter applies to message retrieval (15 req/10s IP, 20 req/10s account)
  - Audit logging for message access (privacy compliance per FR-016)
  - Guest privacy noted in Operational Risks (GDPR/CCPA compliance required)

### Principle IV: Test-Driven Development ✅ PASS

- **Requirement**: >80% coverage (unit, integration, MCP, E2E)
- **Compliance**: User Story 3 explicitly targets 80% coverage improvement
- **Evidence**:
  - FR-012: Maintain ≥80% overall coverage
  - FR-013: Edge case tests (boundary conditions, empty results, null values, limits)
  - FR-014: Error path tests (auth failures, API errors, timeouts)
  - FR-015: Integration tests for new features
  - SC-005: ≥90% coverage for new v1.1 features

### Principle V: Async Performance ✅ PASS

- **Requirement**: Async I/O, httpx.AsyncClient, connection pooling, <500ms p95
- **Compliance**: v1.1 extends v1.0 async infrastructure
- **Evidence**:
  - All new endpoints `async def`
  - Existing `httpx.AsyncClient` with connection pooling (50 max, 20 keep-alive) handles message API calls
  - Performance targets: <2s message retrieval, <5s batch (both well under <500ms per-request p95)
  - Existing retry logic (exponential backoff) applies to message endpoints

### Summary: ✅ ALL GATES PASS - Proceed to Phase 0 Research

No constitutional violations. v1.1 is purely additive, leveraging v1.0 compliant infrastructure.

## Project Structure

### Documentation (this feature)

```
specs/002-enhance-the-hostaway/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output (API discovery, patterns)
├── data-model.md        # Phase 1 output (entities, validation)
├── quickstart.md        # Phase 1 output (usage examples)
├── contracts/           # Phase 1 output (OpenAPI schemas)
│   ├── messages.yaml    # Message retrieval endpoints
│   └── batch.yaml       # Partial failure response schemas
├── checklists/          # Quality gates
│   └── requirements.md  # Spec validation (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── api/
│   ├── main.py                    # FastAPI app (existing)
│   └── routes/
│       ├── auth.py                # Existing v1.0
│       ├── listings.py            # Existing v1.0
│       ├── bookings.py            # Existing v1.0
│       ├── financial.py           # Existing v1.0
│       └── messages.py            # NEW v1.1 - message retrieval routes
├── models/
│   ├── auth.py                    # Existing v1.0
│   ├── listings.py                # Existing v1.0
│   ├── bookings.py                # Existing v1.0
│   ├── financial.py               # Existing v1.0
│   ├── messages.py                # NEW v1.1 - Message, ConversationThread
│   ├── batch.py                   # NEW v1.1 - PartialFailureResponse, BatchItem
│   └── search.py                  # NEW v1.1 - MessageSearchCriteria
├── services/
│   ├── hostaway_client.py         # EXTEND v1.1 - add message methods
│   └── rate_limiter.py            # Existing v1.0 (reuse)
└── mcp/
    ├── server.py                  # EXTEND v1.1 - register message tools
    ├── auth.py                    # Existing v1.0 (reuse)
    ├── config.py                  # Existing v1.0 (reuse)
    └── security.py                # Existing v1.0 (reuse)

tests/
├── unit/
│   ├── test_messages.py           # NEW v1.1 - Message model tests
│   ├── test_batch.py              # NEW v1.1 - PartialFailureResponse tests
│   ├── test_message_search.py     # NEW v1.1 - Search criteria tests
│   └── test_hostaway_client.py    # EXTEND v1.1 - message method tests
├── integration/
│   ├── test_messages_api.py       # NEW v1.1 - message endpoint tests
│   ├── test_batch_failures.py     # NEW v1.1 - partial failure tests
│   └── test_edge_cases.py         # NEW v1.1 - boundary conditions
├── mcp/
│   └── test_message_tools.py      # NEW v1.1 - MCP tool invocation
└── e2e/
    └── test_guest_communication.py # NEW v1.1 - end-to-end workflow
```

**Structure Decision**: Single project structure (Option 1). v1.1 extends existing v1.0 architecture by adding new modules (`messages.py`, `batch.py`, `search.py`) and routes (`messages.py`). No new directories required. Follows v1.0 pattern: models → services → routes → MCP tools.

## Complexity Tracking

*No constitutional violations - this section not required.*

v1.1 maintains v1.0 simplicity principles:
- Single FastAPI application (no microservices)
- Stateless design (no database)
- Reuses existing auth, rate limiting, error handling
- Adds only essential models for message retrieval and partial failures

## Phase 0: Research & Discovery

**Objective**: Resolve unknowns and validate technical assumptions before design.

### Research Tasks

#### R1: Hostaway Messages API Discovery

**Question**: Does Hostaway API provide message retrieval endpoints for all channels (email, SMS, in-app, platform messaging)?

**Research Approach**:
1. Review Hostaway API documentation at https://api.hostaway.com/documentation
2. Search for message/conversation endpoints
3. Identify available channels (email, SMS, in-app, etc.)
4. Document endpoint paths, request/response schemas, pagination support
5. Test with API key from v1.0 deployment

**Deliverables**:
- List of available message endpoints (GET /messages, GET /conversations, etc.)
- Channel support matrix (email: ✓, SMS: ✓, in-app: ?, platform: ?)
- Pagination mechanism (limit/offset vs cursor-based)
- Response schema samples

#### R2: Multi-Channel Consolidation Patterns

**Question**: How to merge messages from multiple channels into chronological timeline?

**Research Approach**:
1. Analyze Hostaway API response structure for different channels
2. Identify common metadata fields (timestamp, sender, content, channel_type)
3. Research timestamp handling (timezone awareness, missing timestamps)
4. Evaluate deduplication strategies (message ID, content hash)
5. Review industry patterns (Slack, Intercom, Zendesk)

**Deliverables**:
- Consolidation algorithm pseudocode
- Edge case handling rules (missing timestamps → retrieval order, duplicates → dedupe by ID)
- Timestamp normalization approach (UTC conversion)

#### R3: Partial Failure Response Design

**Question**: What's the optimal structure for PartialFailureResponse to support batch operations?

**Research Approach**:
1. Review v1.0 error handling patterns
2. Analyze FastAPI best practices for batch responses
3. Research industry standards (Google Cloud, AWS SDK batch responses)
4. Evaluate error categorization taxonomies (not_found, unauthorized, rate_limit, timeout, validation_error)
5. Design actionable error messages with remediation guidance

**Deliverables**:
- PartialFailureResponse Pydantic model design
- Error categorization schema
- Sample responses for different failure scenarios
- Integration approach with existing v1.0 error handling

#### R4: Test Coverage Strategy

**Question**: How to increase coverage from 72.80% to ≥80% focusing on edge cases and error paths?

**Research Approach**:
1. Analyze v1.0 coverage report to identify gaps (likely in error paths, boundary conditions)
2. Research pytest best practices for edge case testing
3. Evaluate mocking strategies for Hostaway API failures (httpx-mock, respx)
4. Design parametrized tests for boundary conditions (empty lists, null values, max limits)
5. Plan error path coverage (auth failures, API errors, timeouts, rate limits)

**Deliverables**:
- Coverage gap analysis (specific modules/functions below 80%)
- Edge case test matrix (empty results, special characters, pagination limits, concurrent access)
- Error path test matrix (401, 403, 404, 429, 500, timeout, network error)
- Parametrized test templates

### Research Outputs

All findings will be documented in `/Users/darrenmorgan/AI_Projects/hostaway-mcp/specs/002-enhance-the-hostaway/research.md` with format:

```markdown
## Decision: [Topic]
**Rationale**: [Why this approach]
**Alternatives Considered**: [Other options]
**Implementation Notes**: [Key details]
```

## Phase 1: Design & Contracts

**Prerequisites**: `research.md` complete with all R1-R4 findings

### D1: Data Model Design

**Input**: Research findings from R1 (Hostaway API schemas), R2 (consolidation patterns)

**Entities to Model**:

1. **Message** (from FR-001 to FR-006, FR-016, FR-018)
   - `id`: str - Unique message identifier
   - `booking_id`: int - Associated booking
   - `content`: str - Message text
   - `timestamp`: datetime - When message sent (timezone-aware)
   - `channel`: MessageChannel (enum) - email | sms | in_app | platform
   - `sender_type`: SenderType (enum) - guest | system | property_manager
   - `sender_id`: str - Sender identifier
   - `recipient_id`: str - Recipient identifier
   - `delivery_status`: DeliveryStatus (enum) - sent | delivered | failed | read
   - Validation: content non-empty, timestamp required, channel from enum

2. **ConversationThread** (from FR-004, FR-006)
   - `booking_id`: int - Primary key for conversation
   - `messages`: List[Message] - Ordered chronologically
   - `total_count`: int - Total messages in thread
   - `channels_used`: Set[MessageChannel] - Channels present in conversation
   - Validation: messages ordered by timestamp, booking_id > 0

3. **PartialFailureResponse** (from FR-007 to FR-011)
   - `successful_results`: List[Any] - Successfully processed items
   - `failed_items`: List[BatchFailure] - Failed items with errors
   - `summary`: BatchSummary - Metrics (total, succeeded, failed)
   - Validation: total = succeeded + failed

4. **BatchFailure** (from FR-008, FR-011)
   - `item_id`: str - Identifier of failed item
   - `error_type`: ErrorType (enum) - not_found | validation_error | rate_limit | timeout | unauthorized
   - `error_message`: str - Human-readable error
   - `remediation`: str - Actionable guidance

5. **BatchSummary** (from FR-010)
   - `total_attempted`: int - Total items in batch
   - `succeeded`: int - Successful items
   - `failed`: int - Failed items
   - `success_rate`: float - succeeded / total_attempted

6. **MessageSearchCriteria** (from FR-001 to FR-003, FR-017)
   - `booking_id`: Optional[int] - Filter by booking
   - `guest_name`: Optional[str] - Partial match search
   - `start_date`: Optional[date] - Date range start
   - `end_date`: Optional[date] - Date range end
   - `channels`: Optional[List[MessageChannel]] - Filter by channels
   - `limit`: int = 50 - Pagination page size (default 50, max 1000)
   - `offset`: int = 0 - Pagination offset
   - Validation: limit ≤ 1000, end_date >= start_date

**Output**: `/Users/darrenmorgan/AI_Projects/hostaway-mcp/specs/002-enhance-the-hostaway/data-model.md`

### D2: API Contracts Generation

**Input**: Functional requirements FR-001 to FR-018, data model from D1

**Endpoints to Design** (all in `/src/api/routes/messages.py`):

1. **GET /api/messages**
   - Query params: booking_id, guest_name, start_date, end_date, channels[], limit, offset
   - Response: `PartialFailureResponse[List[Message]]` (supports partial failures if multi-channel retrieval)
   - Operation ID: `search_messages`
   - Tags: ["messages"]
   - Description: "Search messages across all channels with filters" (from FR-001 to FR-003)

2. **GET /api/messages/conversation/{booking_id}**
   - Path param: booking_id (int)
   - Query params: limit, offset
   - Response: `ConversationThread`
   - Operation ID: `get_conversation_history`
   - Tags: ["messages"]
   - Description: "Retrieve complete conversation history for a booking" (from FR-004, FR-006)

3. **GET /api/batch/properties** (ENHANCE existing endpoint)
   - Query params: property_ids[] (List[int])
   - Response: `PartialFailureResponse[List[Property]]` (replace existing simple List response)
   - Operation ID: `batch_get_properties`
   - Description: "Retrieve multiple properties with partial failure support" (from FR-007 to FR-011)

4. **GET /api/batch/bookings** (ENHANCE existing endpoint)
   - Query params: booking_ids[] (List[int])
   - Response: `PartialFailureResponse[List[Booking]]`
   - Operation ID: `batch_get_bookings`
   - Description: "Retrieve multiple bookings with partial failure support"

**OpenAPI Schemas** (output to `/Users/darrenmorgan/AI_Projects/hostaway-mcp/specs/002-enhance-the-hostaway/contracts/`):

- `messages.yaml` - Message retrieval endpoints
- `batch.yaml` - Partial failure response schemas (reusable across endpoints)

**MCP Tool Auto-Generation**:
- `search_messages` → MCP tool (from GET /api/messages)
- `get_conversation_history` → MCP tool (from GET /api/messages/conversation/{booking_id})
- `batch_get_properties` → MCP tool (enhanced)
- `batch_get_bookings` → MCP tool (enhanced)

**Output**: `/Users/darrenmorgan/AI_Projects/hostaway-mcp/specs/002-enhance-the-hostaway/contracts/*.yaml`

### D3: Quickstart Guide

**Input**: API contracts from D2, data model from D1

**Content**:
1. **Setup**: Prerequisites (v1.0 deployed, API key configured)
2. **Example 1: Search Messages by Booking ID**
   ```python
   # MCP tool invocation
   search_messages(booking_id=12345)

   # Expected response
   {
     "successful_results": [...],
     "failed_items": [],
     "summary": {"total_attempted": 1, "succeeded": 1, "failed": 0}
   }
   ```

3. **Example 2: Get Conversation History**
   ```python
   # MCP tool invocation
   get_conversation_history(booking_id=12345)

   # Expected response
   {
     "booking_id": 12345,
     "messages": [...],
     "total_count": 15,
     "channels_used": ["email", "sms"]
   }
   ```

4. **Example 3: Batch Operation with Partial Failures**
   ```python
   # MCP tool invocation
   batch_get_properties(property_ids=[101, 102, 999, 104])  # 999 is invalid

   # Expected response
   {
     "successful_results": [Property(101), Property(102), Property(104)],
     "failed_items": [{
       "item_id": "999",
       "error_type": "not_found",
       "error_message": "Property 999 not found",
       "remediation": "Verify property ID exists in Hostaway"
     }],
     "summary": {"total_attempted": 4, "succeeded": 3, "failed": 1, "success_rate": 0.75}
   }
   ```

5. **Edge Cases**: Empty results, pagination, special characters in guest names

**Output**: `/Users/darrenmorgan/AI_Projects/hostaway-mcp/specs/002-enhance-the-hostaway/quickstart.md`

### D4: Agent Context Update

**Action**: Run `.specify/scripts/bash/update-agent-context.sh claude`

**Purpose**: Update `.claude/CLAUDE.md` with v1.1 technology additions (if any new libraries required from research)

**Expected Updates**:
- If R1 reveals new Hostaway SDK → add to dependencies
- If R3 introduces new error handling library → document
- If R4 adds new testing tools (httpx-mock, respx) → list in test infrastructure

**Preservation**: Manual additions between `<!-- AGENT_CONTEXT_START -->` and `<!-- AGENT_CONTEXT_END -->` markers remain untouched

**Output**: Updated `.claude/CLAUDE.md` (only if new tech identified)

## Post-Phase 1: Re-evaluate Constitution Check

After completing Phase 1 (research, data model, contracts), re-verify constitutional compliance:

### ✅ Principle I: API-First Design - CONFIRMED
- All endpoints designed with operation_id, Pydantic models, docstrings
- Contracts documented in OpenAPI YAML
- MCP tools auto-generated from FastAPI routes

### ✅ Principle II: Type Safety - CONFIRMED
- All models use Pydantic with Field constraints
- Enums defined (MessageChannel, SenderType, DeliveryStatus, ErrorType)
- Response models specified for all endpoints

### ✅ Principle III: Security by Default - CONFIRMED
- Authentication reuses v1.0 API key middleware
- Input validation via Pydantic SearchCriteria model
- Rate limiting applies (existing v1.0 infrastructure)
- Audit logging planned for message access (privacy compliance)

### ✅ Principle IV: Test-Driven Development - CONFIRMED
- Test strategy defined in R4 (coverage plan, edge cases, error paths)
- ≥80% target documented in FR-012
- Test files identified in Project Structure

### ✅ Principle V: Async Performance - CONFIRMED
- All new endpoints async def
- httpx.AsyncClient reused for Hostaway API calls
- Performance targets <2s, <5s within <500ms p95 per-request

**Result**: ✅ ALL GATES PASS POST-DESIGN - Proceed to Phase 2 (Tasks)

## Next Steps

**Phase 1 Complete** - Generated Artifacts:
- ✅ `/Users/darrenmorgan/AI_Projects/hostaway-mcp/specs/002-enhance-the-hostaway/research.md`
- ✅ `/Users/darrenmorgan/AI_Projects/hostaway-mcp/specs/002-enhance-the-hostaway/data-model.md`
- ✅ `/Users/darrenmorgan/AI_Projects/hostaway-mcp/specs/002-enhance-the-hostaway/contracts/*.yaml`
- ✅ `/Users/darrenmorgan/AI_Projects/hostaway-mcp/specs/002-enhance-the-hostaway/quickstart.md`
- ✅ Updated `.claude/CLAUDE.md` (if applicable)

**Phase 2: Task Breakdown** (separate command):
- Run `/speckit.tasks` to generate dependency-ordered implementation tasks
- Tasks will reference data-model.md, contracts/, and research.md
- Expected output: `/Users/darrenmorgan/AI_Projects/hostaway-mcp/specs/002-enhance-the-hostaway/tasks.md`

**Ready for**: `/speckit.tasks` command to proceed with implementation planning.
