# Feature 003 Summary: Multi-Tenant Billable MCP Server

**Status**: ✅ Specification Complete (Updated with Tech Stack)
**Date**: 2025-10-13
**Branch**: `003-we-need-to`

---

## Overview

Transform the Hostaway MCP Server from single-tenant prototype to production-ready SaaS platform with:
- **Multi-tenant architecture**: Organizations connect their own Hostaway accounts with Supabase RLS-enforced data isolation
- **Stripe billing**: Per-listing subscription model ($X/listing/month) with automatic metering
- **Self-service dashboard**: Next.js/Vercel dashboard for API key management, usage metrics, billing history
- **AI-powered property management**: Listing creation, batch updates, financial analysis via MCP tools

## Tech Stack Decisions

**Database & Auth: Supabase**
- PostgreSQL with Row Level Security (RLS) for multi-tenancy
- Supabase Auth for user authentication (email/password, OAuth)
- Supabase Vault (pgsodium) for Hostaway credential encryption
- Edge Functions for Stripe webhook handling
- MCP tools for schema management

**Frontend: Vercel + Next.js**
- Next.js 14 App Router for dashboard UI
- Server Components + Server Actions
- Deployed on Vercel (edge runtime)

**Backend: FastAPI MCP Server (Existing)**
- Validates X-API-Key against Supabase
- Retrieves encrypted credentials from Supabase
- Proxies to Hostaway API with org-scoped data

**Billing: Stripe**
- Subscription billing with quantity metering
- Webhooks via Supabase Edge Functions

---

## User Stories (Priority Order)

1. **P1 - Account Connection** 🔐
   - Users securely connect Hostaway credentials (account ID + secret key)
   - Complete data isolation between tenants
   - Credential validation via test API call

2. **P2 - API Key Management** 🔑
   - Web dashboard for key generation/regeneration/deletion
   - Display full key only once with copy action
   - Max 5 active keys per user

3. **P3 - Per-Listing Billing** 💳
   - Stripe subscription with quantity = active listing count
   - Daily sync job updates billing quantity with proration
   - Payment failure suspends API access

4. **P4 - Usage Metrics** 📊
   - Dashboard shows: API requests, listing count, projected bill, 30-day chart
   - Billing history with downloadable invoices
   - Manual "Sync Now" for listing count refresh

5. **P5 - AI Operations** 🤖
   - MCP tools for listing creation, batch updates, financial analysis
   - All operations scoped to user's Hostaway account
   - Uses PartialFailureResponse pattern from v1.1

---

## Key Requirements (27 Total)

### Multi-Tenancy (FR-001 to FR-004, FR-023)
- Organization isolation via Supabase RLS policies
- Supabase Vault (pgsodium) encrypted credentials
- Credential validation on connection
- Per-organization MCP tool scoping
- Database-level RLS enforcement on all tables

### API Keys (FR-005 to FR-008, FR-024)
- Next.js dashboard (Vercel) for key management
- Show full key only at generation
- Max 5 keys per organization
- Immediate invalidation on delete/regenerate
- Supabase Auth JWT for dashboard sessions

### Billing (FR-009 to FR-013, FR-025)
- Stripe subscription per-listing model
- Daily listing count sync with proration
- Supabase Edge Functions for webhook handling
- API suspension on payment failure
- Cancel subscription at period end
- Webhook signature verification + idempotent processing

### Metrics (FR-014 to FR-016)
- Track: API requests, listing count, projected bill
- Billing history with PDF receipts
- Manual sync trigger

### MCP Operations (FR-017 to FR-019, FR-026)
- Existing v1.0/v1.1 tools scoped to organization
- New tools: create_listing, batch_update_listings, get_financial_summary
- FastAPI queries Supabase for API key validation + credential retrieval

### Security (FR-020 to FR-022, FR-027)
- X-API-Key authentication against Supabase
- Audit logging to Supabase (organization_id, tool, timestamp)
- Never log/expose credentials
- FastAPI uses Supabase service role key to bypass RLS for auth

---

## Success Criteria

| ID | Metric | Target |
|----|--------|--------|
| SC-001 | Onboarding time | <3 minutes (signup → first API key) |
| SC-002 | Multi-tenant isolation | 100% (no data leakage across 10+ users) |
| SC-003 | Billing accuracy | 99.9% (Stripe quantity matches Hostaway count) |
| SC-004 | Payment failure handling | <5 min (API suspension + restoration) |
| SC-005 | Dashboard load time | <1s (p95) |
| SC-006 | API key generation | <2s |
| SC-007 | Listing count sync | <30s (up to 500 listings) |
| SC-008 | Concurrent load | 1000 requests across 100 users (no errors) |
| SC-009 | Support ticket reduction | 80% (via self-service dashboard) |
| SC-010 | AI operation success rate | 95% (when credentials valid) |

---

## Key Entities (Supabase Schema)

**Supabase Auth** (auth schema):
1. **auth.users**: Managed by Supabase Auth (id, email, encrypted_password, email_confirmed_at, last_sign_in_at)

**Application Tables** (public schema with RLS):
2. **organizations**: Tenant entity (id PK, name, owner_user_id FK, created_at, stripe_customer_id)
3. **organization_members**: User-org relationship (organization_id, user_id FK, role, joined_at)
4. **hostaway_credentials**: Encrypted Hostaway creds (id PK, organization_id FK, account_id, encrypted_secret_key via Vault, credentials_valid, last_validated_at)
5. **api_keys**: MCP tokens (id PK, organization_id FK, key_hash SHA-256, created_at, last_used_at, is_active, created_by_user_id FK)
6. **subscriptions**: Stripe billing (id PK, organization_id FK, stripe_subscription_id, current_quantity, status, billing_period_start/end)
7. **usage_metrics**: Aggregated usage (id PK, organization_id FK, month_year, total_api_requests, unique_tools_used, listing_count_snapshot)
8. **audit_logs**: MCP invocation logs (id PK, organization_id FK, user_id FK nullable, tool_name, request_params JSONB, response_status, error_message nullable, created_at)

---

## Edge Cases Covered

- ✅ Credential expiration/revocation (401 detection → suspend access → email notification)
- ✅ Listing count discrepancies (daily reconciliation with audit log)
- ✅ Payment failures after retries (suspend API → archive data → 30-day retention)
- ✅ Multi-account requests (1:1 user-account mapping, future enhancement for switching)
- ✅ Deleted listings (daily sync reduces Stripe quantity with proration)
- ✅ Rate limit handling (per-user tracking, 429 with retry-after)
- ✅ API key limit (max 5, require deletion before new generation)
- ✅ Batch operation failures (PartialFailureResponse pattern from v1.1)

---

## Validation Results

**Requirements Checklist**: ✅ 100/100
- No implementation details ✅
- All requirements testable ✅
- Success criteria measurable ✅
- User-centric language ✅
- Prioritized user stories ✅
- Edge cases addressed ✅
- Security considerations ✅
- Dependencies identified ✅
- No critical ambiguities ✅
- Specification complete ✅

---

## Tech Stack Costs

| Service | Tier | Cost | Limits |
|---------|------|------|--------|
| **Supabase** | Free | $0/month | 500MB DB, 50K MAUs, 2GB storage, 5GB bandwidth |
| | Pro | $25/month | 8GB DB, unlimited auth, 50GB storage, 250GB bandwidth |
| **Vercel** | Hobby | $0/month | 100GB bandwidth, unlimited sites |
| | Pro | $20/month | 1TB bandwidth, advanced analytics |
| **Stripe** | Pay-as-you-go | 2.9% + $0.30 per transaction | - |
| **VPS (existing)** | Hostinger | ~$10/month | FastAPI MCP Server |
| **Total (Launch)** | | **$10-35/month** | vs Clerk alternative: $45+/month |

## Next Steps

1. **Run `/speckit.plan`** to generate implementation plan with:
   - **Phase 0 Research**: Supabase RLS patterns, Supabase Vault encryption, Stripe subscription API, Next.js 14 App Router patterns
   - **Phase 1 Design**:
     - Supabase schema with RLS policies (use MCP tools for migrations)
     - Next.js dashboard wireframes + components
     - FastAPI-Supabase integration patterns
     - Stripe webhook Edge Function design
   - **Phase 2+ Implementation**: Staged rollout (P1 → P2 → P3 → P4 → P5)

2. **Supabase Setup (Phase 0)**:
   - Initialize Supabase project via CLI
   - Enable pgsodium extension for credential encryption
   - Create database schema using Supabase MCP tools
   - Design RLS policies for organization isolation
   - Setup Supabase Auth with email/password provider

3. **Next.js Dashboard (Phase 1)**:
   - Bootstrap Next.js 14 project with App Router
   - Install @supabase/ssr for Server Components
   - Design dashboard layouts (API keys, billing, metrics)
   - Implement Supabase Auth integration

4. **FastAPI Integration (Phase 1)**:
   - Install supabase-py in FastAPI server
   - Update API key validation to query Supabase
   - Implement credential decryption from Vault
   - Add audit logging to Supabase

5. **Stripe Integration (Phase 2)**:
   - Create Supabase Edge Function for webhooks
   - Implement subscription creation/update logic
   - Setup daily listing count sync job

---

**Specification Status**: ✅ READY FOR PLANNING (Tech Stack: Supabase + Vercel + FastAPI)
