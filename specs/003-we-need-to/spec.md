# Feature Specification: Multi-Tenant Billable MCP Server

**Feature Branch**: `003-we-need-to`
**Created**: 2025-10-13
**Status**: Validated ✅
**Input**: User description: "we need to build out the mcp so that end users can connect their own account, we need metrics and billing with stripe and a simple dashboard where they can get their api key. we need a model where we bill per listing. this will be a billable mcp server for hosts to use ai against their hostaway account to perform listing creation, updates, financial analysis and more as we add more endpoints."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Hostaway Account Connection & Authentication (Priority: P1)

Property managers need to securely connect their own Hostaway credentials to the MCP server so they can use AI-powered tools against their specific Hostaway account data without sharing credentials with other users.

**Why this priority**: Without multi-tenant account isolation, the system cannot serve multiple users. This is the foundation for all other features and delivers immediate value by allowing users to authenticate their own accounts.

**Independent Test**: Can be fully tested by registering a new user, connecting their Hostaway account (OAuth or API credentials), and verifying isolation - user A cannot access user B's data. Delivers value by securing multi-tenant access.

**Acceptance Scenarios**:

1. **Given** a new property manager visits the dashboard, **When** they sign up and connect their Hostaway account ID and secret key, **Then** the system stores encrypted credentials scoped to their user account and validates credentials by making a test API call to Hostaway
2. **Given** a user has connected their Hostaway account, **When** they make MCP tool calls using their API key, **Then** the system uses their specific Hostaway credentials for all API requests and returns only their property data
3. **Given** two users (User A and User B) have connected different Hostaway accounts, **When** User A makes an MCP request, **Then** the system never exposes User B's data or credentials to User A

---

### User Story 2 - API Key Management & Dashboard Access (Priority: P2)

Users need a simple web dashboard where they can generate, view, and regenerate their MCP API keys so they can configure their AI agents to access the billable MCP server.

**Why this priority**: After account connection (P1), users need a way to get API keys to actually use the service. This enables self-service onboarding and delivers immediate value by letting users configure AI tools.

**Independent Test**: Can be tested by logging into dashboard, generating an API key, copying it, and successfully using it in an MCP client (Claude Desktop). Delivers value by enabling self-service access without manual intervention.

**Acceptance Scenarios**:

1. **Given** a user is logged into the dashboard, **When** they navigate to the API Keys section, **Then** the system displays a "Generate API Key" button and any existing active keys (masked, showing only last 4 characters)
2. **Given** a user clicks "Generate API Key", **When** the key is created, **Then** the system displays the full key once (with a "Copy" button) and warns "Store this securely - you won't see it again"
3. **Given** a user has an active API key, **When** they click "Regenerate", **Then** the system invalidates the old key, generates a new one, and displays a confirmation that the old key will stop working immediately
4. **Given** a user wants to revoke access, **When** they delete an API key, **Then** the system immediately invalidates the key and any subsequent MCP requests using that key return 401 Unauthorized

---

### User Story 3 - Per-Listing Billing with Stripe (Priority: P3)

Users are billed monthly based on the number of active listings in their Hostaway account, with automatic metering via Stripe subscriptions, so they pay fairly for the resources they consume without manual invoicing.

**Why this priority**: After users can connect accounts (P1) and get API keys (P2), billing enables monetization. This is the revenue model foundation but can be implemented after core functionality is proven.

**Independent Test**: Can be tested by connecting a Hostaway account with 5 listings, verifying Stripe subscription is created with quantity=5, adding 2 listings to Hostaway, and confirming Stripe subscription updates to quantity=7 with prorated charges. Delivers value by automating billing.

**Acceptance Scenarios**:

1. **Given** a new user connects their Hostaway account with 10 active listings, **When** they complete onboarding, **Then** the system creates a Stripe subscription with quantity=10 and bills them $X per listing per month (e.g., $5/listing/month = $50/month)
2. **Given** a user's listing count changes (they add or remove listings in Hostaway), **When** the system's daily sync job runs, **Then** Stripe subscription quantity updates automatically and prorated charges/credits are applied to the next invoice
3. **Given** a user's payment fails, **When** Stripe webhook notifies payment failure, **Then** the system suspends their API key access and sends email notification with payment retry instructions
4. **Given** a user wants to cancel, **When** they click "Cancel Subscription" in the dashboard, **Then** Stripe subscription is canceled at period end and the user retains access until the billing cycle completes

---

### User Story 4 - Usage Metrics & Monitoring Dashboard (Priority: P4)

Users need visibility into their API usage, listing count, and billing history via a dashboard so they can monitor costs, track AI tool usage, and validate billing accuracy.

**Why this priority**: After billing is active (P3), users need transparency for trust and cost management. This is a quality-of-life feature that reduces support burden but isn't critical for launch.

**Independent Test**: Can be tested by making 100 MCP API calls, viewing the dashboard, and verifying metrics show 100 requests, current listing count, current month's projected bill, and past invoices. Delivers value by providing cost visibility.

**Acceptance Scenarios**:

1. **Given** a user is logged into the dashboard, **When** they view the Usage tab, **Then** the system displays current month's API request count, current active listing count, projected bill for current month, and a 30-day request volume chart
2. **Given** a user wants to audit billing, **When** they view the Billing History section, **Then** the system displays past Stripe invoices with date, listing count, amount charged, and payment status
3. **Given** a user's listing count is shown as 15 but they believe it's incorrect, **When** they click "Sync Now", **Then** the system immediately fetches latest listing count from Hostaway API and updates the display

---

### User Story 5 - AI-Powered Listing Operations via MCP (Priority: P5)

Users can perform listing creation, updates, and financial analysis via AI agents using MCP tools, with all operations scoped to their authenticated Hostaway account, enabling scalable property management automation.

**Why this priority**: This is the value-add feature that differentiates the service, but it builds on all previous infrastructure (P1-P4). Can be incrementally added as new MCP endpoints are developed.

**Independent Test**: Can be tested by connecting a test Hostaway account, using Claude Desktop with the MCP server to create a new listing via natural language ("Create a 2-bedroom listing in Miami"), and verifying the listing appears in Hostaway under the correct account. Delivers value by enabling AI-powered property management.

**Acceptance Scenarios**:

1. **Given** a user has configured their AI agent with their MCP API key, **When** they ask "Create a new 3-bedroom listing in Austin, TX", **Then** the AI agent uses the create_listing MCP tool with the user's Hostaway credentials and the listing appears in their Hostaway account
2. **Given** a user wants to update pricing across all listings, **When** they ask "Increase all nightly rates by 10%", **Then** the AI agent uses batch_update_listings MCP tool and confirms updates for each listing with success/failure status
3. **Given** a user wants financial insights, **When** they ask "What's my total revenue this month?", **Then** the AI agent uses get_financial_summary MCP tool and returns revenue broken down by listing with booking counts and average nightly rate

---

### Edge Cases

- **What happens when a user's Hostaway credentials expire or are revoked?** System detects 401 errors from Hostaway API, marks account as "Credentials Invalid", suspends MCP API access, and sends email prompting credential re-entry
- **How does the system handle listing count discrepancies (Hostaway shows 10, Stripe subscription shows 8)?** Daily sync job reconciles counts, updates Stripe subscription quantity with proration, and logs discrepancy for audit trail
- **What if a user connects multiple Hostaway accounts?** System supports 1:1 user-to-Hostaway-account mapping initially; multi-account support requires account switching UI (future enhancement)
- **How are deleted listings handled for billing?** Daily sync job detects listing deletions via Hostaway API, reduces Stripe subscription quantity, applies prorated credit to next invoice
- **What happens when Stripe subscription payment fails after retries?** After final retry failure (per Stripe retry logic), system suspends API key access, archives user data, sends cancellation notice with 30-day data retention policy
- **How does the system handle API rate limits across multiple tenants?** Each user's MCP requests count against their Hostaway account's rate limit (20 req/10s); system tracks per-user rate limit state and returns 429 with retry-after guidance when limits are hit
- **What if a user generates 100 API keys?** System limits to 5 active API keys per user; attempting to generate 6th key requires deleting an existing key first
- **How are partial failures handled in batch listing operations?** Uses PartialFailureResponse pattern from v1.1 - returns successful operations alongside detailed failure info with remediation guidance

## Technical Architecture *(decided)*

### Tech Stack

**Database & Auth: Supabase**
- PostgreSQL database with Row Level Security (RLS) for multi-tenancy
- Supabase Auth for user authentication (email/password, OAuth providers)
- Supabase Vault (pgsodium) for Hostaway credential encryption
- Edge Functions for Stripe webhook handling
- MCP integration available for schema management during development

**Frontend: Vercel + Next.js**
- Next.js 14 with App Router for dashboard UI
- Server Components for data fetching from Supabase
- Server Actions for Stripe operations
- Deployed on Vercel (edge runtime for API routes)

**Backend: FastAPI MCP Server (Existing)**
- Continues to handle MCP tool operations
- Validates X-API-Key against Supabase database
- Fetches organization's Hostaway credentials from Supabase
- Proxies authenticated requests to Hostaway API

**Billing: Stripe**
- Subscription-based billing with per-listing metering
- Webhooks handled by Supabase Edge Functions
- Customer portal for payment management

### Multi-Tenancy Strategy

**Row Level Security (RLS) Enforcement:**
```sql
-- All tables use RLS to enforce organization isolation
-- Policies automatically filter data by user's organization_id
-- Database-level security (cannot be bypassed by application code)
```

**Data Isolation Flow:**
1. User authenticates via Supabase Auth → gets JWT with user_id
2. Application queries organizations table → RLS policy filters by user's org membership
3. All child tables (api_keys, subscriptions, etc.) filtered by organization_id
4. Zero trust: even compromised application code cannot access other orgs' data

### Security Architecture

**Authentication Layers:**
- **Dashboard Access**: Supabase Auth JWT tokens (session-based)
- **MCP Tool Access**: X-API-Key header (static keys for Claude Desktop)

**Credential Storage:**
- Hostaway account credentials encrypted using Supabase Vault (pgsodium)
- Encryption keys managed by Supabase (hardware security module backed)
- Decryption only happens in backend FastAPI when validating MCP requests

**Audit Trail:**
- All MCP tool invocations logged with organization_id, user_id, tool_name, timestamp
- Supabase audit logs track dashboard access and data modifications

## Requirements *(mandatory)*

### Functional Requirements

**Multi-Tenancy & Authentication**
- **FR-001**: System MUST support multiple isolated organizations via Supabase Auth, where each organization's data, credentials, and API access are completely isolated using Row Level Security (RLS) policies
- **FR-002**: System MUST allow organizations to securely store Hostaway account credentials (account ID + secret key) encrypted at rest using Supabase Vault (pgsodium extension)
- **FR-003**: System MUST validate Hostaway credentials on connection by making a test API call (e.g., GET /v1/listings with limit=1) and rejecting invalid credentials
- **FR-004**: System MUST scope all MCP tool operations to the authenticated organization's Hostaway credentials - Organization A can never access Organization B's Hostaway data
- **FR-023**: System MUST enforce data isolation at the database layer using Supabase RLS policies on all tables (organizations, api_keys, hostaway_credentials, subscriptions, usage_metrics)

**API Key Management**
- **FR-005**: System MUST provide a Next.js web dashboard (deployed on Vercel) where authenticated users can generate, view (masked), regenerate, and delete their MCP API keys
- **FR-006**: System MUST display full API key only once at generation time with a "Copy to clipboard" action and clear warning about secure storage
- **FR-007**: System MUST support up to 5 active API keys per organization for different AI agent configurations
- **FR-008**: System MUST immediately invalidate API keys upon deletion or regeneration, causing subsequent MCP requests to return 401 Unauthorized
- **FR-024**: Dashboard MUST use Supabase Auth for user authentication with JWT tokens for session management

**Billing & Subscriptions**
- **FR-009**: System MUST integrate with Stripe to create subscription-based billing where organizations are charged monthly per active listing (e.g., $5/listing/month)
- **FR-010**: System MUST automatically sync listing count from Hostaway daily (via scheduled job) and update Stripe subscription quantity with prorated charges/credits
- **FR-011**: System MUST handle Stripe webhook events using Supabase Edge Functions for payment success, payment failure, subscription cancellation, and subscription updated
- **FR-012**: System MUST suspend MCP API access (by marking api_keys.is_active=false) when Stripe subscription payment fails and restore access when payment succeeds
- **FR-013**: System MUST allow users to cancel subscriptions via dashboard, retaining access until current billing period ends
- **FR-025**: Stripe webhook Edge Function MUST verify webhook signatures and update Supabase database with idempotent operations (preventing duplicate processing)

**Usage Metrics & Monitoring**
- **FR-014**: System MUST track and display per-user metrics: total API requests (current month), active listing count, projected monthly bill, and request volume chart (30-day)
- **FR-015**: System MUST provide billing history showing past invoices with date, listing count, amount charged, payment status, and downloadable PDF receipt
- **FR-016**: System MUST provide a "Sync Now" action to manually trigger listing count refresh from Hostaway API for billing validation

**MCP Tool Operations**
- **FR-017**: System MUST expose existing v1.0/v1.1 MCP tools (properties, bookings, messages) scoped to the authenticated organization's Hostaway account
- **FR-018**: System MUST add new MCP tools for listing creation (create_listing), batch updates (batch_update_listings), and financial analysis (get_financial_summary) using organization's Hostaway credentials
- **FR-019**: System MUST return organization-specific data only - MCP tool responses filtered by the API key's associated organization_id
- **FR-026**: FastAPI MCP server MUST query Supabase to validate X-API-Key and retrieve associated organization's encrypted Hostaway credentials before each MCP tool invocation

**Security & Compliance**
- **FR-020**: System MUST authenticate all MCP API requests using X-API-Key header validation against active API keys stored in Supabase
- **FR-021**: System MUST log all MCP tool invocations to Supabase with organization_id, tool name, timestamp, and success/failure status for audit trail
- **FR-022**: System MUST encrypt Hostaway credentials at rest using Supabase Vault and never log or expose them in API responses or error messages
- **FR-027**: System MUST use Supabase service role key in FastAPI backend to bypass RLS when validating API keys (read-only access to api_keys and hostaway_credentials tables)

### Key Entities (Supabase Schema)

**Managed by Supabase Auth** (auth schema):
- **auth.users**: User authentication data (id, email, encrypted_password, email_confirmed_at, last_sign_in_at) - managed by Supabase Auth

**Custom Application Tables** (public schema):
- **organizations**: Tenant entity with id (PK), name, owner_user_id (FK to auth.users), created_at, stripe_customer_id
- **organization_members**: Many-to-many relationship with organization_id, user_id (FK to auth.users), role (owner/admin/member), joined_at
- **hostaway_credentials**: Encrypted credentials with id (PK), organization_id (FK), account_id (text), encrypted_secret_key (vault encrypted), credentials_valid (boolean), last_validated_at, created_at
- **api_keys**: MCP authentication tokens with id (PK), organization_id (FK), key_hash (SHA-256), created_at, last_used_at, is_active (boolean), created_by_user_id (FK to auth.users)
- **subscriptions**: Stripe billing with id (PK), organization_id (FK), stripe_subscription_id, current_quantity (listing count), status (active/past_due/canceled/trialing), billing_period_start, billing_period_end, created_at
- **usage_metrics**: Aggregated usage with id (PK), organization_id (FK), month_year (YYYY-MM), total_api_requests, unique_tools_used, listing_count_snapshot, created_at
- **audit_logs**: MCP tool invocation logs with id (PK), organization_id (FK), user_id (FK to auth.users, nullable), tool_name, request_params (JSONB), response_status, error_message (nullable), created_at

**RLS Policies Applied To**:
- All public schema tables filtered by organization_id via user's organization membership
- Enforced at database level (cannot be bypassed by application)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can sign up via Supabase Auth, connect their Hostaway account, and generate their first API key in under 3 minutes from initial signup
- **SC-002**: Multi-tenant isolation verified - 100% of MCP requests return data only from the authenticated organization's Hostaway account (tested with 10+ concurrent organizations, RLS policies enforced)
- **SC-003**: Billing accuracy validated - Stripe subscription quantity matches Hostaway listing count with 99.9% accuracy across daily sync jobs
- **SC-004**: Payment failure handling tested - API access suspended within 5 minutes of Stripe payment failure webhook (Supabase Edge Function) and restored within 5 minutes of successful payment retry
- **SC-005**: Next.js dashboard (deployed on Vercel) loads in under 1 second (p95) showing current metrics: API usage, listing count, projected bill
- **SC-006**: API key generation completes in under 2 seconds with immediate usability in MCP clients (Claude Desktop)
- **SC-007**: Listing count sync completes in under 30 seconds for organizations with up to 500 listings
- **SC-008**: System handles 1000 concurrent MCP requests across 100 different organizations without data leakage or credential mix-ups (RLS enforcement tested)
- **SC-009**: Reduce billing support tickets by 80% through self-service Next.js dashboard with real-time usage visibility and invoice download
- **SC-010**: AI-powered listing operations (create, update, analyze) succeed with 95% success rate when Hostaway credentials are valid
