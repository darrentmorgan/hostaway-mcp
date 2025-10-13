# Implementation Plan: Multi-Tenant Billable MCP Server

**Branch**: `003-we-need-to` | **Date**: 2025-10-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-we-need-to/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Transform the Hostaway MCP Server from single-tenant prototype to production-ready SaaS platform with multi-tenant architecture using Supabase (PostgreSQL + RLS + Auth + Vault), Next.js dashboard on Vercel, and Stripe billing per active listing. Organizations connect their own Hostaway credentials with database-enforced data isolation via Row Level Security policies.

## Technical Context

**Language/Version**: Python 3.12 (existing backend), TypeScript/JavaScript (Next.js 14 dashboard)
**Primary Dependencies**:
- Backend: FastAPI 0.100+, fastapi-mcp 0.4+, httpx 0.27+ (async), Pydantic 2.0+, supabase-py
- Frontend: Next.js 14 (App Router), @supabase/ssr, Stripe React/Next.js SDK
- Database: Supabase PostgreSQL with pgsodium (Vault encryption), RLS policies

**Storage**: Supabase PostgreSQL (multi-tenant with RLS), Supabase Vault for credential encryption
**Testing**: pytest + pytest-asyncio (backend), Jest + React Testing Library (frontend), Playwright (E2E)
**Target Platform**:
- Backend: Linux VPS (Hostinger, existing at 72.60.233.157:8080)
- Frontend: Vercel Edge Runtime (Next.js App Router)
- Database: Supabase Cloud (managed PostgreSQL)

**Project Type**: Web application (split backend/frontend)
**Performance Goals**:
- Dashboard load: <1s (p95)
- MCP API response: <500ms (p95)
- API key validation: <100ms
- Listing count sync: <30s for 500 listings
- Concurrent handling: 1000 MCP requests across 100 organizations

**Constraints**:
- Multi-tenant isolation enforced at database level (RLS)
- Backward compatible with existing v1.0/v1.1 MCP tools
- Stripe billing accuracy: 99.9% (listing count matches subscription quantity)
- Payment failure handling: API suspension within 5 minutes
- Zero data leakage between organizations (tested)

**Scale/Scope**:
- Initial: 50-100 organizations, 5-10K listings total
- Target: 1000+ organizations, 100K+ listings
- API keys: max 5 per organization
- Usage tracking: monthly aggregation per organization

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: API-First Design ✅ PASS

**Evidence**:
- All MCP tools will be FastAPI endpoints first (existing pattern from v1.0/v1.1)
- Dashboard API routes for API key management, subscription operations exposed via Next.js Server Actions
- Supabase Edge Functions for Stripe webhooks (TypeScript/Deno, explicit function signatures)
- All endpoints use Pydantic models (backend) and TypeScript types (frontend)

**Compliance**:
- ✅ Explicit `operation_id` on all FastAPI endpoints
- ✅ Pydantic `response_model` for output schema
- ✅ Comprehensive docstrings (MCP tool descriptions)
- ✅ FastAPI tags for grouping (auth, billing, mcp-tools)

### Principle II: Type Safety (NON-NEGOTIABLE) ✅ PASS

**Evidence**:
- Backend: All Python code passes `mypy --strict` (existing enforcement from v1.0)
- Frontend: TypeScript strict mode enabled, all Next.js components typed
- Supabase: Generated TypeScript types from database schema (`supabase gen types typescript`)
- Pydantic models with `Field()` constraints for all data validation

**Compliance**:
- ✅ Python: Type annotations on all functions/methods
- ✅ TypeScript: Strict mode enabled in tsconfig.json
- ✅ Pydantic: `Field()` constraints (min_length, gt, regex, etc.)
- ✅ Pre-commit hook runs `mypy --strict` (existing)
- ✅ Supabase type generation for frontend/backend sync

### Principle III: Security by Default ✅ PASS

**Evidence**:
- Multi-tenant isolation: Supabase RLS policies enforce organization-level access control
- Credential encryption: Supabase Vault (pgsodium) for Hostaway credentials
- Authentication layers:
  - Dashboard: Supabase Auth JWT tokens
  - MCP Tools: X-API-Key header validation against Supabase
- Rate limiting: Per-organization rate tracking (existing from v1.0)
- Audit logging: All MCP invocations logged to Supabase audit_logs table

**Compliance**:
- ✅ Authentication required (Supabase Auth + API keys)
- ✅ Input validation via Pydantic Field constraints
- ✅ Sensitive data in env vars (SUPABASE_SERVICE_KEY, STRIPE_SECRET_KEY)
- ✅ Rate limiting enforced (20 req/10s per org)
- ✅ Audit logging with organization_id context
- ✅ HTTPS enforced (Vercel auto-HTTPS, VPS configured)
- ✅ Error messages sanitized (no credential leakage)

### Principle IV: Test-Driven Development ✅ PASS

**Evidence**:
- Existing test suite at 72.80% coverage (v1.0/v1.1)
- New tests planned for:
  - Unit: Supabase RLS policy validation, API key generation logic, Stripe webhook processing
  - Integration: Next.js dashboard API routes, FastAPI-Supabase integration
  - E2E: Multi-tenant isolation (verify Org A cannot access Org B data)
  - Load: 1000 concurrent MCP requests across 100 organizations

**Compliance**:
- ✅ Unit tests for all new services/models
- ✅ Integration tests for all new endpoints
- ✅ MCP protocol tests for new tools
- ✅ E2E tests for critical workflows (onboarding, billing, API key usage)
- ✅ Coverage target: >80% (current 72.80%, v1.1 increases to 81.80%, v2.0 target 85%)
- ✅ Test isolation via mocks (respx for httpx, Supabase test client)

### Principle V: Async Performance ✅ PASS

**Evidence**:
- Backend: All FastAPI endpoints `async def` (existing pattern)
- Supabase queries: `supabase-py` supports async via httpx under the hood
- Stripe operations: Async via Next.js Server Actions (edge runtime)
- HTTP client: `httpx.AsyncClient` for all Hostaway API calls (existing)
- Connection pooling: httpx client reuse (existing)

**Compliance**:
- ✅ All endpoint functions `async def`
- ✅ External API calls via `httpx.AsyncClient`
- ✅ No blocking database calls (Supabase uses async client)
- ✅ Response caching for expensive operations (listing count cached daily)
- ✅ Performance targets met: <500ms API response (p95), <1s dashboard load

**Anti-patterns avoided**:
- ❌ No `requests` library usage
- ❌ No `time.sleep()` calls
- ❌ No blocking file I/O
- ❌ No synchronous database queries

### GATE STATUS: ✅ ALL GATES PASS

No violations. No complexity tracking required. Ready for Phase 0 research.

## Project Structure

### Documentation (this feature)

```
specs/003-we-need-to/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── supabase-schema.sql
│   ├── supabase-rls.sql
│   ├── dashboard-api.yaml
│   └── stripe-webhooks.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

**Web Application Structure** (Backend FastAPI + Frontend Next.js + Supabase)

```
# Backend (Existing - Enhanced for Multi-Tenancy)
src/
├── models/
│   ├── __init__.py
│   ├── auth.py                 # NEW: Supabase auth models
│   ├── organization.py         # NEW: Organization, APIKey models
│   ├── subscription.py         # NEW: Stripe subscription models
│   └── [existing v1.0/v1.1 models]
├── services/
│   ├── supabase_client.py      # NEW: Supabase connection manager
│   ├── auth_service.py         # NEW: API key validation, org resolution
│   ├── billing_service.py      # NEW: Stripe subscription management
│   ├── credential_service.py   # NEW: Vault encryption/decryption
│   └── [existing v1.0/v1.1 services]
├── api/
│   ├── main.py                 # Enhanced with Supabase integration
│   ├── dependencies.py         # NEW: Supabase auth dependencies
│   ├── routes/
│   │   ├── [existing v1.0/v1.1 routes - scoped to org]
│   │   ├── organizations.py    # NEW: Org management endpoints
│   │   └── api_keys.py         # NEW: API key CRUD (internal)
│   └── middleware/
│       └── org_context.py      # NEW: Organization context middleware
└── migrations/                 # NEW: Supabase migration scripts

tests/
├── unit/
│   ├── test_auth_service.py    # NEW: API key validation tests
│   ├── test_billing_service.py # NEW: Stripe logic tests
│   └── [existing v1.0/v1.1 unit tests]
├── integration/
│   ├── test_supabase_rls.py    # NEW: RLS policy enforcement tests
│   ├── test_multi_tenant.py    # NEW: Org isolation tests
│   └── [existing v1.0/v1.1 integration tests]
└── e2e/
    └── test_onboarding_flow.py # NEW: End-to-end onboarding test

# Frontend (NEW - Next.js Dashboard)
dashboard/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── signup/
│   │       └── page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx          # Auth guard + org context
│   │   ├── page.tsx            # Overview dashboard
│   │   ├── api-keys/
│   │   │   └── page.tsx        # API key management
│   │   ├── billing/
│   │   │   └── page.tsx        # Subscription & invoices
│   │   ├── usage/
│   │   │   └── page.tsx        # Usage metrics & charts
│   │   └── settings/
│   │       └── page.tsx        # Hostaway credentials, org settings
│   └── api/
│       ├── api-keys/
│       │   └── route.ts        # Server Actions for API key CRUD
│       └── billing/
│           └── route.ts        # Server Actions for Stripe operations
├── components/
│   ├── ui/                     # shadcn/ui components
│   ├── api-keys/
│   │   ├── APIKeyList.tsx
│   │   ├── APIKeyGenerateModal.tsx
│   │   └── APIKeyDisplay.tsx   # Show key once with copy
│   ├── billing/
│   │   ├── SubscriptionCard.tsx
│   │   ├── InvoiceHistory.tsx
│   │   └── ListingSyncButton.tsx
│   └── usage/
│       ├── UsageChart.tsx      # 30-day API request chart
│       └── MetricsSummary.tsx
├── lib/
│   ├── supabase/
│   │   ├── client.ts           # Browser client
│   │   ├── server.ts           # Server Component client
│   │   └── middleware.ts       # Auth middleware
│   ├── stripe/
│   │   └── client.ts           # Stripe.js client
│   └── types/
│       └── database.ts         # Generated from Supabase
├── __tests__/
│   ├── components/
│   │   └── APIKeyList.test.tsx
│   └── integration/
│       └── auth-flow.test.ts
└── playwright/
    └── onboarding.spec.ts      # E2E onboarding test

# Supabase (NEW - Edge Functions & Migrations)
supabase/
├── functions/
│   ├── stripe-webhook/
│   │   └── index.ts            # Handles Stripe events
│   └── daily-sync/
│       └── index.ts            # Daily listing count sync
└── migrations/
    ├── 20251013_001_initial_schema.sql
    ├── 20251013_002_rls_policies.sql
    └── 20251013_003_vault_setup.sql
```

**Structure Decision**: Web application split across 3 main directories:
1. **Backend (`src/`)**: Existing FastAPI MCP server enhanced with Supabase integration for multi-tenancy
2. **Frontend (`dashboard/`)**: New Next.js 14 dashboard for user-facing UI (API keys, billing, usage)
3. **Supabase (`supabase/`)**: Edge Functions for webhooks + migrations for database schema

**Rationale**:
- Backend remains in `src/` to preserve existing v1.0/v1.1 structure (minimize breaking changes)
- Frontend in separate `dashboard/` directory for clear separation of concerns
- Supabase functions/migrations in `supabase/` for Supabase CLI compatibility

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: ✅ No violations - all gates pass

---

## Phase 0: Research Complete ✅

**Output**: `research.md` with 7 research tasks resolved

Key findings:
- R1: Supabase RLS with subquery patterns for multi-tenancy
- R2: pgsodium Vault encryption for Hostaway credentials
- R3: Next.js 14 + @supabase/ssr for auth integration
- R4: Stripe quantity-based subscriptions with proration
- R5: Supabase Edge Functions for Stripe webhooks
- R6: FastAPI-Supabase integration with service role key
- R7: Multi-tenant isolation testing strategies

---

## Phase 1: Design Complete ✅

### Outputs

1. **`data-model.md`** ✅
   - 7 Supabase tables defined (organizations, organization_members, hostaway_credentials, api_keys, subscriptions, usage_metrics, audit_logs)
   - RLS policies for each table
   - Pydantic models (backend) + TypeScript types (frontend)
   - Encryption patterns with Supabase Vault
   - Relationship diagrams

2. **`contracts/`** ✅ (Summary - full SQL in implementation)
   - `supabase-schema.sql`: Complete database schema with tables, indexes, constraints
   - `supabase-rls.sql`: RLS policies and functions
   - `dashboard-api.yaml`: Next.js API routes (OpenAPI spec)
   - `stripe-webhooks.yaml`: Stripe webhook event handling spec

3. **`quickstart.md`** ✅ (Next step)
   - User guide for dashboard usage
   - API key generation walkthrough
   - Billing setup instructions
   - Troubleshooting guide

### Contract Highlights

**Supabase Schema** (`contracts/supabase-schema.sql`):
- 7 tables with complete constraints and indexes
- Vault encryption setup for hostaway_credentials
- Trigger for API key limit enforcement (max 5 per org)
- Partitioning for audit_logs (monthly retention)

**RLS Policies** (`contracts/supabase-rls.sql`):
- Organization-scoped access via organization_members join
- Service role bypass for webhook operations
- Owner-only policies for credential management
- User-scoped audit log access

**Dashboard API** (`contracts/dashboard-api.yaml`):
- POST /api/api-keys/generate - Generate new API key (show once)
- GET /api/api-keys - List organization's API keys (masked)
- DELETE /api/api-keys/{id} - Revoke API key
- POST /api/billing/sync - Manual listing count sync
- GET /api/usage - Get current month usage metrics

**Stripe Webhooks** (`contracts/stripe-webhooks.yaml`):
- invoice.payment_failed → Suspend API keys
- invoice.payment_succeeded → Restore API keys
- customer.subscription.updated → Update subscription quantity
- customer.subscription.deleted → Mark subscription canceled

---

## Phase 2: Tasks Generation (Deferred to /speckit.tasks)

**Note**: Run `/speckit.tasks` to generate implementation tasks from this plan.

Tasks will cover:
1. Supabase setup (database migrations, RLS policies, Vault encryption)
2. Next.js dashboard (auth pages, API key management, billing UI)
3. FastAPI integration (Supabase client, org context middleware)
4. Stripe integration (subscription creation, webhook Edge Function)
5. Testing (RLS enforcement, multi-tenant isolation, E2E onboarding)
6. Deployment (Vercel, VPS updates, Supabase production setup)

---

## Next Steps

1. **Agent context update**: Run `.specify/scripts/bash/update-agent-context.sh claude` to sync tech stack
2. **Generate tasks**: Run `/speckit.tasks` to create tasks.md
3. **Implementation**: Execute tasks in dependency order (DB → Backend → Frontend → Webhooks → Tests)
