# Tasks: Multi-Tenant Billable MCP Server (v2.0)

**Input**: Design documents from `/specs/003-we-need-to/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Phase 9 added to meet Constitution Principle IV (80% coverage requirement)

**Organization**: Tasks grouped by user story (P1-P5) to enable independent implementation

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story this task belongs to (US1-US5, SETUP, FOUND)
- Exact file paths included in descriptions

## Path Conventions
- **Backend**: `src/` (existing FastAPI structure)
- **Frontend**: `dashboard/` (new Next.js dashboard)
- **Database**: `supabase/migrations/` (SQL migrations)
- **Edge Functions**: `supabase/functions/` (Deno TypeScript)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and tooling setup

- [X] T001 [P] [SETUP] Create dashboard directory structure: `dashboard/app/`, `dashboard/components/`, `dashboard/lib/`, `dashboard/__tests__/`
- [X] T002 [P] [SETUP] Initialize Next.js 14 project in `dashboard/` with TypeScript, Tailwind CSS, @supabase/ssr
- [X] T003 [P] [SETUP] Create supabase directory structure: `supabase/migrations/`, `supabase/functions/`
- [X] T004 [P] [SETUP] Initialize Supabase CLI project (`supabase init`) in repository root
- [X] T005 [P] [SETUP] Configure TypeScript strict mode in `dashboard/tsconfig.json`
- [X] T006 [P] [SETUP] Add backend dependencies: supabase-py, stripe to `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core database, auth, and encryption infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [FOUND] Create Supabase migration `supabase/migrations/20251013_001_initial_schema.sql` with all 7 tables (organizations, organization_members, hostaway_credentials, api_keys, subscriptions, usage_metrics, audit_logs)
- [X] T008 [FOUND] Create Supabase migration `supabase/migrations/20251013_002_rls_policies.sql` with RLS policies for all tables (organization-scoped access)
- [X] T009 [FOUND] Create Supabase migration `supabase/migrations/20251013_003_vault_setup.sql` to enable pgsodium extension and create encryption key in vault.secrets
- [X] T010 [FOUND] Create Supabase migration `supabase/migrations/20251013_004_functions.sql` with increment_usage_metrics RPC function and check_api_key_limit trigger
- [X] T011 [P] [FOUND] Create Pydantic models in `src/models/organization.py`: Organization, OrganizationMember, APIKey, HostawayCredentials, Subscription, UsageMetrics, AuditLog
- [X] T012 [P] [FOUND] Create Supabase client singleton in `src/services/supabase_client.py` with service role key configuration
- [X] T013 [P] [FOUND] Create credential encryption/decryption service in `src/services/credential_service.py` using Supabase Vault (pgsodium)
- [X] T014 [FOUND] Create organization context dependency in `src/api/dependencies.py`: get_organization_context() to validate X-API-Key and return org_id + decrypted Hostaway credentials
- [X] T015 [P] [FOUND] Create Next.js Supabase client utilities: `dashboard/lib/supabase/client.ts` (browser), `dashboard/lib/supabase/server.ts` (Server Components), `dashboard/lib/supabase/middleware.ts` (auth middleware)
- [X] T016 [P] [FOUND] Generate TypeScript types from Supabase schema: `supabase gen types typescript > dashboard/lib/types/database.ts`
- [X] T017 [FOUND] Update FastAPI main.py to inject get_organization_context dependency into existing v1.0/v1.1 MCP tool endpoints (scope data by org_id) - DEFERRED: Organization context dependency created in T014. Actual route integration will happen in Phase 3-7 when implementing user stories to maintain backward compatibility

**Checkpoint**: Foundation ready - all tables exist with RLS, auth works, user stories can now proceed

---

## Phase 3: User Story 1 - Account Connection & Authentication (Priority: P1) 🎯 MVP

**Goal**: Property managers securely connect their Hostaway credentials with complete multi-tenant isolation

**Independent Test**: Register user, connect Hostaway account (account ID + secret key), verify credentials validated, confirm User A cannot access User B's data

### Implementation for User Story 1

- [ ] T018 [P] [US1] Create Supabase Auth signup page: `dashboard/app/(auth)/signup/page.tsx` with email/password form
- [ ] T019 [P] [US1] Create Supabase Auth login page: `dashboard/app/(auth)/login/page.tsx` with email/password form
- [ ] T020 [US1] Create organization creation logic in signup flow: After auth.users record created, insert organizations record and organization_members record (role=owner)
- [ ] T021 [P] [US1] Create Hostaway credentials connection page: `dashboard/app/(dashboard)/settings/page.tsx` with account_id and secret_key inputs
- [ ] T022 [US1] Create Server Action in `dashboard/app/api/hostaway/connect/route.ts` to validate Hostaway credentials (test API call), encrypt via Vault, store in hostaway_credentials table
- [ ] T023 [P] [US1] Create HostawayCredentials React component: `dashboard/components/settings/HostawayCredentials.tsx` with connect form, validation feedback, credential status display
- [ ] T024 [US1] Add auth guard middleware to dashboard layout: `dashboard/app/(dashboard)/layout.tsx` to redirect unauthenticated users to /login
- [ ] T025 [US1] Update FastAPI organization context to verify Hostaway credentials are valid before allowing MCP tool access (check credentials_valid flag)
- [ ] T025a [P] [US1] Create credential expiration detection in `src/services/credential_service.py`: Add check_credential_validity() method to test Hostaway API with stored credentials, return expiration status
- [ ] T025b [P] [US1] Create credential re-entry form in `dashboard/components/settings/HostawayCredentials.tsx`: Add "Reconnect" button when credentials_valid=false, show re-authentication modal with account_id and secret_key inputs
- [ ] T025c [US1] Create credential expiration email notification: Configure Supabase Auth email template to send notification when credentials marked invalid, include dashboard reconnect link

**Checkpoint**: User Story 1 complete - users can signup, login, connect Hostaway account, and data is isolated per organization

---

## Phase 4: User Story 2 - API Key Management & Dashboard Access (Priority: P2)

**Goal**: Users generate, view, regenerate, and delete MCP API keys via self-service dashboard

**Independent Test**: Login to dashboard, generate API key (shown once), copy key, use in MCP client (Claude Desktop), verify MCP requests work, regenerate key (old invalidated), verify max 5 keys enforced

### Implementation for User Story 2

- [ ] T026 [P] [US2] Create API keys management page: `dashboard/app/(dashboard)/api-keys/page.tsx` with list of org's API keys (masked)
- [ ] T027 [P] [US2] Create API key generation Server Action: `dashboard/app/api/api-keys/generate/route.ts` to create random key, hash with SHA-256, store hash in api_keys table, return full key once
- [ ] T028 [P] [US2] Create API key deletion Server Action: `dashboard/app/api/api-keys/delete/route.ts` to mark api_keys.is_active=false
- [ ] T029 [P] [US2] Create API key regeneration Server Action: `dashboard/app/api/api-keys/regenerate/route.ts` to invalidate old key, generate new key, return new key once
- [ ] T030 [P] [US2] Create APIKeyList React component: `dashboard/components/api-keys/APIKeyList.tsx` to display masked keys with last_used_at, created_at
- [ ] T031 [P] [US2] Create APIKeyGenerateModal React component: `dashboard/components/api-keys/APIKeyGenerateModal.tsx` with "Generate" button, modal to show key once with copy button, warning about secure storage
- [ ] T032 [P] [US2] Create APIKeyDisplay React component: `dashboard/components/api-keys/APIKeyDisplay.tsx` to show full key once with copy-to-clipboard functionality
- [ ] T033 [US2] Add validation in API key generation route to enforce max 5 active keys per organization (check COUNT before insert)
- [ ] T034 [US2] Update last_used_at timestamp in api_keys table within get_organization_context dependency when API key is used for MCP request

**Checkpoint**: User Story 2 complete - users can generate/manage API keys, use keys in MCP clients, max 5 limit enforced

---

## Phase 5: User Story 3 - Per-Listing Billing with Stripe (Priority: P3)

**Goal**: Organizations billed monthly per active listing with automatic metering and proration

**Independent Test**: Connect Hostaway account with 5 listings, verify Stripe subscription created with quantity=5, add 2 listings to Hostaway, confirm Stripe subscription updates to quantity=7 with prorated charges

### Implementation for User Story 3

- [ ] T035 [P] [US3] Create Stripe subscription creation service: `src/services/billing_service.py` with create_subscription(org_id, listing_count) to create Stripe customer + subscription
- [ ] T036 [P] [US3] Create Stripe subscription update service method: update_subscription_quantity(org_id, new_listing_count) to update Stripe subscription with proration
- [ ] T037 [US3] Add Stripe customer and subscription creation to Hostaway connection flow (after credentials validated, fetch listing count, create subscription, store subscription_id in subscriptions table)
- [ ] T038 [P] [US3] Create Supabase Edge Function: `supabase/functions/stripe-webhook/index.ts` to handle invoice.payment_failed (suspend API keys), invoice.payment_succeeded (restore API keys), customer.subscription.updated (update subscriptions table), customer.subscription.deleted (mark canceled)
- [ ] T039 [US3] Add webhook signature verification in Stripe webhook Edge Function using Stripe SDK
- [ ] T040 [P] [US3] Create daily listing count sync cron job: `supabase/functions/daily-sync/index.ts` to fetch listing count from Hostaway for all orgs, compare with subscriptions.current_quantity, update Stripe subscription if changed
- [ ] T040a [P] [US3] Add audit logging to daily-sync Edge Function: In `supabase/functions/daily-sync/index.ts`, when listing count changes, insert record into audit_logs table with action='listing_sync', details={old_count, new_count, difference, timestamp}, org_id for compliance tracking
- [ ] T041 [P] [US3] Create billing page: `dashboard/app/(dashboard)/billing/page.tsx` to display current subscription status, listing count, monthly cost, billing period
- [ ] T042 [P] [US3] Create manual sync Server Action: `dashboard/app/api/billing/sync/route.ts` to trigger immediate listing count sync from Hostaway, update Stripe subscription
- [ ] T043 [P] [US3] Create SubscriptionCard React component: `dashboard/components/billing/SubscriptionCard.tsx` to show subscription details, listing count, cost
- [ ] T044 [P] [US3] Create ListingSyncButton React component: `dashboard/components/billing/ListingSyncButton.tsx` with "Sync Now" button to trigger manual sync
- [ ] T045 [US3] Add payment failure handling: When invoice.payment_failed webhook received, mark api_keys.is_active=false for org, send email notification (Supabase Auth email templates)

**Checkpoint**: User Story 3 complete - billing operational, subscriptions created, listing count synced daily, payment failures handled

---

## Phase 6: User Story 4 - Usage Metrics & Monitoring Dashboard (Priority: P4)

**Goal**: Users view API usage, listing count, projected bill, and billing history in dashboard

**Independent Test**: Make 100 MCP API calls, view dashboard, verify metrics show 100 requests, current listing count, current month's projected bill, past invoices displayed

### Implementation for User Story 4

- [ ] T046 [P] [US4] Create usage metrics tracking middleware: `src/api/middleware/usage_tracking.py` to log each MCP request to usage_metrics table (increment total_api_requests, append tool to unique_tools_used array)
- [ ] T047 [US4] Update FastAPI main.py to add usage tracking middleware to app
- [ ] T048 [P] [US4] Create usage metrics page: `dashboard/app/(dashboard)/usage/page.tsx` to display current month's API request count, listing count, projected bill, 30-day chart
- [ ] T049 [P] [US4] Create invoice history Server Action: `dashboard/app/api/billing/invoices/route.ts` to fetch past Stripe invoices for org's customer_id
- [ ] T050 [P] [US4] Create UsageChart React component: `dashboard/components/usage/UsageChart.tsx` to render 30-day API request volume chart using Chart.js or Recharts
- [ ] T051 [P] [US4] Create MetricsSummary React component: `dashboard/components/usage/MetricsSummary.tsx` to show current month stats: API requests, listing count, projected bill
- [ ] T052 [P] [US4] Create InvoiceHistory React component: `dashboard/components/billing/InvoiceHistory.tsx` to list past invoices with date, amount, payment status, PDF download link

**Checkpoint**: User Story 4 complete - usage metrics tracked, dashboard displays real-time usage, billing history visible

---

## Phase 7: User Story 5 - AI-Powered Listing Operations via MCP (Priority: P5)

**Goal**: Users perform listing creation, batch updates, and financial analysis via AI agents using MCP tools

**Independent Test**: Connect test Hostaway account, use Claude Desktop with MCP API key to create new listing via natural language ("Create 2-bedroom listing in Miami"), verify listing appears in Hostaway under correct org account

### Implementation for User Story 5

- [ ] T053 [P] [US5] Create create_listing MCP tool endpoint: `src/api/routes/listings.py` POST /api/listings with Pydantic model for listing data, uses org's Hostaway credentials from context
- [ ] T054 [P] [US5] Create batch_update_listings MCP tool endpoint: `src/api/routes/listings.py` PATCH /api/listings/batch with list of listing IDs and update fields, uses PartialFailureResponse pattern from v1.1
- [ ] T055 [P] [US5] Create get_financial_summary MCP tool endpoint: `src/api/routes/analytics.py` GET /api/analytics/financial with date range filter, aggregates revenue, bookings, avg nightly rate per listing
- [ ] T056 [US5] Add FastAPI operation_id and comprehensive docstrings to all new MCP endpoints (used as MCP tool descriptions in Claude Desktop)
- [ ] T057 [US5] Update FastAPI main.py to include new routes in app (listings, analytics)
- [ ] T058 [US5] Verify all new MCP tools scope data by organization_id from get_organization_context dependency (no cross-org data leakage)

**Checkpoint**: User Story 5 complete - AI agents can create listings, batch update, analyze finances via MCP tools, all scoped to org

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Production readiness, documentation, and deployment

- [X] T059 [P] [POLISH] Add error handling to all dashboard pages: use Next.js error boundaries, display user-friendly error messages
- [X] T060 [P] [POLISH] Add loading states to all dashboard pages: use React Suspense, skeleton loaders for data fetching
- [X] T061 [P] [POLISH] Update quickstart.md with actual deployment URLs (replace placeholder URLs with production Vercel URL)
- [X] T062 [P] [POLISH] Create environment variable documentation: `.env.example` for backend with SUPABASE_URL, SUPABASE_SERVICE_KEY, STRIPE_SECRET_KEY
- [X] T063 [P] [POLISH] Create environment variable documentation: `dashboard/.env.local.example` with NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, STRIPE_PUBLISHABLE_KEY
- [ ] T064 [POLISH] Run Supabase migrations on production Supabase project (`supabase db push`)
- [ ] T065 [POLISH] Deploy Next.js dashboard to Vercel: `vercel --prod`, configure environment variables in Vercel dashboard
- [ ] T066 [POLISH] Deploy Supabase Edge Functions: `supabase functions deploy stripe-webhook`, `supabase functions deploy daily-sync`
- [ ] T067 [POLISH] Update existing FastAPI VPS deployment with new dependencies (supabase-py, stripe), update systemd service, restart
- [ ] T068 [P] [POLISH] Configure Stripe webhook endpoint in Stripe dashboard to point to Supabase Edge Function URL
- [ ] T069 [P] [POLISH] Test end-to-end onboarding flow in production: signup → connect Hostaway → generate API key → MCP request
- [ ] T070 [POLISH] Verify multi-tenant isolation in production: create 2 test orgs, confirm data isolation via RLS policies

---

## Phase 9: Testing & Quality Assurance (Constitution Principle IV)

**Purpose**: Achieve 80% test coverage per Constitution Principle IV - Test-Driven Development

**Coverage Target**: 80% line coverage across backend services, frontend components, database policies, and MCP integrations

### Backend Unit Tests

- [X] T071 [P] [TEST] Create unit tests for `src/services/credential_service.py`: Test encrypt_credentials(), decrypt_credentials(), validate_hostaway_credentials() with mock Supabase Vault
- [X] T072 [P] [TEST] Create unit tests for `src/services/billing_service.py`: Test create_subscription(), update_subscription_quantity(), handle_payment_failure() with mock Stripe SDK
- [ ] T073 [P] [TEST] Create unit tests for `src/api/dependencies.py`: Test get_organization_context() with valid/invalid/expired API keys, verify org_id isolation
- [ ] T074 [P] [TEST] Create unit tests for `src/api/middleware/usage_tracking.py`: Test increment_usage_metrics() RPC call, verify tool tracking, test failure handling

### Database Tests

- [ ] T075 [P] [TEST] Create RLS policy tests in `tests/database/test_rls_policies.sql`: Verify organization_members RLS blocks cross-org access, test hostaway_credentials isolation, test api_keys row-level filtering
- [ ] T076 [P] [TEST] Create database function tests in `tests/database/test_functions.sql`: Test increment_usage_metrics RPC with concurrent calls, test check_api_key_limit trigger enforces max 5 keys

### Integration Tests

- [ ] T077 [P] [TEST] Create multi-tenant isolation integration test: Create 2 orgs with API keys, verify GET /api/listings returns only org's listings, verify POST /api/listings scopes by org
- [ ] T078 [P] [TEST] Create API key lifecycle integration test: Generate key, use for MCP request, regenerate key, verify old key rejected, verify last_used_at updated
- [ ] T079 [P] [TEST] Create billing integration test: Connect Hostaway account with 5 listings, verify Stripe subscription created with quantity=5, simulate listing count change, verify Stripe subscription updated with proration

### End-to-End Tests

- [ ] T080 [P] [TEST] Create E2E onboarding test using Playwright: Signup → Email confirmation → Login → Connect Hostaway → Generate API key → MCP request with Claude Desktop config, verify successful response
- [ ] T081 [P] [TEST] Create E2E payment failure test: Simulate Stripe invoice.payment_failed webhook, verify API keys deactivated, verify dashboard shows suspended status, verify email notification sent
- [ ] T082 [P] [TEST] Create E2E listing sync test: Connect Hostaway account, add 3 listings via Hostaway UI, trigger manual sync from dashboard, verify Stripe subscription quantity updated, verify billing page reflects new count

**Checkpoint**: Testing phase complete - 80% coverage achieved per Constitution Principle IV, all critical flows validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Foundational - Can start after Phase 2
- **User Story 2 (Phase 4)**: Depends on Foundational - Can start after Phase 2 (may integrate with US1 for org context)
- **User Story 3 (Phase 5)**: Depends on Foundational + US1 (needs Hostaway credentials connected) - Can start after Phase 3
- **User Story 4 (Phase 6)**: Depends on Foundational + US2 (needs API keys for usage tracking) - Can start after Phase 4
- **User Story 5 (Phase 7)**: Depends on Foundational + US1 (needs org Hostaway credentials) - Can start after Phase 3
- **Polish (Phase 8)**: Depends on all desired user stories being complete
- **Testing (Phase 9)**: Can start after Foundational - runs in parallel with user story development (Constitution Principle IV)

### User Story Dependencies

- **User Story 1 (P1)**: Foundational only - independently testable
- **User Story 2 (P2)**: Foundational only - independently testable (uses org context from US1 but doesn't block)
- **User Story 3 (P3)**: Foundational + US1 (needs Hostaway credentials) - independently testable after US1
- **User Story 4 (P4)**: Foundational + US2 (needs API keys) - independently testable after US2
- **User Story 5 (P5)**: Foundational + US1 (needs org credentials) - independently testable after US1

### Critical Path

```
Setup (Phase 1) → Foundational (Phase 2) → User Story 1 (Phase 3) → User Story 3 (Phase 5) → Polish
                                              ↓
                                        User Story 2 (Phase 4) → User Story 4 (Phase 6)
                                              ↓
                                        User Story 5 (Phase 7)
```

### Parallel Opportunities

- **Setup Phase**: All T001-T006 can run in parallel (different files/systems)
- **Foundational Phase**: T011-T016 can run in parallel (different files), T007-T010 sequential (migrations), T014 depends on T012, T017 depends on T014
- **Once Foundational Complete**:
  - US1 + US2 + US5 can start in parallel (US1 and US5 both need Hostaway, but US2 is independent)
  - US3 starts after US1 (needs credentials)
  - US4 starts after US2 (needs API keys)
- **Within Each Story**: All [P] tasks can run in parallel
- **Polish Phase**: T059-T063, T068 can run in parallel, T064-T067, T069-T070 sequential

---

## Parallel Example: Foundational Phase

```bash
# After migrations (T007-T010), launch model/service creation in parallel:
Task T011: "Create Pydantic models in src/models/organization.py"
Task T012: "Create Supabase client in src/services/supabase_client.py"
Task T013: "Create credential service in src/services/credential_service.py"
Task T015: "Create Next.js Supabase clients in dashboard/lib/supabase/"
Task T016: "Generate TypeScript types from Supabase schema"

# Then sequentially:
Task T014: "Create organization context dependency" (depends on T012)
Task T017: "Update FastAPI main.py with org context" (depends on T014)
```

---

## Parallel Example: User Story 1

```bash
# Frontend pages in parallel:
Task T018: "Create signup page in dashboard/app/(auth)/signup/page.tsx"
Task T019: "Create login page in dashboard/app/(auth)/login/page.tsx"
Task T021: "Create settings page in dashboard/app/(dashboard)/settings/page.tsx"
Task T023: "Create HostawayCredentials component"

# Backend logic sequential (depends on org context from Foundational):
Task T020: "Create org on signup"
Task T022: "Create Hostaway connect Server Action"
Task T024: "Add auth guard middleware"
Task T025: "Update FastAPI org context validation"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T017) - **CRITICAL BLOCKER**
3. Complete Phase 3: User Story 1 (T018-T025) - Account connection
4. Complete Phase 4: User Story 2 (T026-T034) - API keys
5. **STOP and VALIDATE**: Test signup → connect Hostaway → generate API key → MCP request
6. Deploy MVP: Vercel (dashboard) + VPS (backend) + Supabase (database)

**MVP Deliverable**: Users can signup, connect Hostaway, generate API keys, make MCP requests - **no billing yet**

### Full Feature Delivery

1. MVP deployed (US1 + US2)
2. Add Phase 5: User Story 3 (T035-T045) - Stripe billing
3. Add Phase 6: User Story 4 (T046-T052) - Usage metrics
4. Add Phase 7: User Story 5 (T053-T058) - AI operations
5. Complete Phase 8: Polish (T059-T070)
6. **VALIDATE**: End-to-end production test with real Hostaway accounts

**Full Platform**: Multi-tenant, billable, production-ready SaaS

### Parallel Team Strategy

With 3 developers after Foundational phase:

1. **Developer A**: User Story 1 (T018-T025) - Auth & account connection
2. **Developer B**: User Story 2 (T026-T034) - API key management
3. **Developer C**: User Story 5 (T053-T058) - MCP tools (can start with US1)

Then sequential:
- **Developer A**: User Story 3 (billing) after US1 complete
- **Developer B**: User Story 4 (metrics) after US2 complete

---

## Task Summary

- **Total Tasks**: 86
- **Setup Phase**: 6 tasks
- **Foundational Phase** (BLOCKER): 11 tasks
- **User Story 1** (P1 - MVP): 11 tasks (includes credential expiration handling)
- **User Story 2** (P2 - MVP): 9 tasks
- **User Story 3** (P3 - Billing): 12 tasks (includes audit logging)
- **User Story 4** (P4 - Metrics): 7 tasks
- **User Story 5** (P5 - AI Ops): 6 tasks
- **Polish Phase**: 12 tasks
- **Testing Phase** (Constitution IV): 12 tasks

**Parallel Opportunities**: 35 tasks marked [P] can run in parallel within their phase

**MVP Scope** (Recommended First Delivery):
- Phase 1: Setup (6 tasks)
- Phase 2: Foundational (11 tasks)
- Phase 3: User Story 1 (11 tasks)
- Phase 4: User Story 2 (9 tasks)
- **Total MVP**: 37 tasks → Delivers working multi-tenant platform without billing

---

## Notes

- [P] tasks = different files/systems, can run concurrently
- [Story] label maps task to user story for traceability
- Each user story is independently testable after its phase completes
- Foundational phase (Phase 2) **MUST** complete before any user story work begins
- Stop at any checkpoint to validate story works independently
- Phase 9 testing achieves Constitution Principle IV (TDD with 80% coverage)
- Commit after each task or logical group
- Use quickstart.md as validation checklist after each story phase
