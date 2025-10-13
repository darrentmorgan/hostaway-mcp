# Quickstart Guide: Multi-Tenant Billable MCP Server (v2.0)

**Date**: 2025-10-13
**Prerequisites**: Supabase account, Stripe account, Vercel account (free tier)

---

## Overview

v2.0 transforms the Hostaway MCP Server into a production SaaS platform with:
- **Multi-tenant architecture**: Organizations connect their own Hostaway accounts
- **Stripe billing**: Per-listing subscription ($5/listing/month)
- **Next.js dashboard**: Self-service API key management, usage metrics, billing
- **Supabase backend**: PostgreSQL with RLS for data isolation

This guide shows how to get started as a property manager using the platform.

---

## Setup for Property Managers

### Step 1: Sign Up & Create Organization

1. Visit dashboard: `https://hostaway-mcp.vercel.app` (or your domain)
2. Click **Sign Up** → Enter email & password
3. Verify email (Supabase Auth sends verification link)
4. On first login, create organization:
   - Organization name: `My Property Management Co`
   - Click **Create Organization**

**What happens**:
- Supabase creates `organizations` record
- You're added to `organization_members` as owner
- Redirected to dashboard home

---

### Step 2: Connect Hostaway Account

1. Navigate to **Settings** → **Hostaway Integration**
2. Enter your Hostaway credentials:
   - Account ID: `ACC_12345` (from Hostaway dashboard)
   - Secret Key: `secret_xxx` (generate in Hostaway → API Keys)
3. Click **Connect & Validate**

**What happens**:
- System makes test API call to Hostaway (`GET /v1/listings?limit=1`)
- If valid: Credentials encrypted via Supabase Vault (pgsodium)
- If invalid: Error shown, retry with correct credentials

**Security Note**: Credentials are encrypted at rest, never exposed in logs or responses

---

### Step 3: Setup Stripe Billing

1. After connecting Hostaway, system fetches listing count
2. Billing setup modal appears:
   - **Listing count detected**: 15 active listings
   - **Monthly cost**: $75/month ($5 × 15 listings)
   - Click **Start Subscription**
3. Stripe Checkout opens:
   - Enter payment method (card or ACH)
   - Confirm subscription
4. Redirected to dashboard on success

**What happens**:
- Stripe customer created with org metadata
- Subscription created with `quantity=15`
- Subscription ID stored in Supabase
- Status: `active` (or `trialing` if trial enabled)

**Billing Details**:
- Prorated charges if listing count changes mid-cycle
- Daily sync updates Stripe subscription quantity
- Automatic proration: Adding 5 listings mid-month = ~$12.50 extra (prorated)

---

### Step 4: Generate API Key for Claude Desktop

1. Navigate to **API Keys** tab
2. Click **Generate New API Key**
3. API key displayed **once** (64 hex characters):
   ```
   api_abc123def456...xyz789
   ```
4. Click **Copy to Clipboard**
5. **Important**: Store securely (you won't see it again!)

**What happens**:
- System generates random 32-byte key → hex string
- SHA-256 hash stored in Supabase (not the key itself)
- Key returned once, then discarded

**Usage in Claude Desktop**:
```json
// ~/.config/Claude/config.json
{
  "mcpServers": {
    "hostaway-mcp": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "X-API-Key: api_abc123def456...xyz789",
        "-H", "Content-Type: application/json",
        "https://mcp.hostaway-server.com/mcp/tools/invoke",
        "-d", "@-"
      ]
    }
  }
}
```

**API Key Limits**:
- Max 5 active keys per organization
- Regenerate if compromised (old key invalidated immediately)
- Monitor `last_used_at` in dashboard

---

## Using the Dashboard

### API Keys Page

**View Keys**:
```
┌─────────────────────────────────────────────────┐
│ API Keys                                        │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                 │
│ Key ending in ...xyz789                         │
│ Created: 2025-10-13 10:30 AM                    │
│ Last used: 2 hours ago                          │
│ [Regenerate] [Delete]                           │
│                                                 │
│ Key ending in ...abc456                         │
│ Created: 2025-10-10 2:15 PM                     │
│ Last used: Never                                │
│ [Regenerate] [Delete]                           │
│                                                 │
│ [+ Generate New API Key] (3/5 used)             │
└─────────────────────────────────────────────────┘
```

**Generate Key**:
1. Click **Generate New API Key**
2. Key displayed in modal (copy immediately)
3. Confirm storage with checkbox
4. Modal closes, key added to list (masked)

**Regenerate Key**:
1. Click **Regenerate** on existing key
2. Confirm warning: "Old key will stop working immediately"
3. New key displayed (copy immediately)
4. Old key invalidated (API requests return 401)

---

### Billing Page

**Subscription Overview**:
```
┌─────────────────────────────────────────────────┐
│ Active Subscription                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                 │
│ Current Billing Period: Oct 1 - Oct 31, 2025   │
│ Active Listings: 15                             │
│ Monthly Cost: $75.00 ($5/listing)               │
│ Next Invoice: Nov 1, 2025                       │
│                                                 │
│ [Sync Listing Count] [Manage in Stripe]         │
└─────────────────────────────────────────────────┘
```

**Manual Sync**:
1. Click **Sync Listing Count**
2. System fetches latest count from Hostaway API
3. If changed: Updates Stripe subscription with proration
4. Toast notification: "Listing count updated: 15 → 18 (+$15 prorated)"

**Invoice History**:
```
┌─────────────────────────────────────────────────┐
│ Invoice History                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                 │
│ Oct 2025 - $75.00 - Paid                        │
│   15 listings × $5/listing                      │
│   [View Invoice PDF]                            │
│                                                 │
│ Sep 2025 - $50.00 - Paid                        │
│   10 listings × $5/listing                      │
│   [View Invoice PDF]                            │
└─────────────────────────────────────────────────┘
```

---

### Usage Metrics Page

**Current Month Usage**:
```
┌─────────────────────────────────────────────────┐
│ Usage - October 2025                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                 │
│ 📊 API Requests: 1,234                          │
│ 📝 Active Listings: 15                          │
│ 💰 Projected Bill: $75.00                       │
│                                                 │
│ 📈 Request Volume (Last 30 Days)                │
│   [Chart showing daily API request counts]      │
│                                                 │
│ 🔧 Tools Used:                                  │
│   - get_properties: 450 calls                   │
│   - create_listing: 12 calls                    │
│   - get_bookings: 200 calls                     │
│   - search_messages: 572 calls                  │
└─────────────────────────────────────────────────┘
```

---

## MCP Tool Usage Examples

### Example 1: Get Properties

**Claude Desktop prompt**:
> "Show me all my active listings in Miami"

**MCP invocation** (automatic via API key):
```bash
curl -X POST \
  -H "X-API-Key: api_abc123..." \
  -H "Content-Type: application/json" \
  https://mcp.hostaway-server.com/api/properties \
  -d '{"city": "Miami"}'
```

**Response**:
```json
{
  "properties": [
    {
      "id": 101,
      "name": "Beach House A",
      "city": "Miami",
      "bedrooms": 3,
      "price_per_night": 250
    },
    {
      "id": 102,
      "name": "Condo Downtown",
      "city": "Miami",
      "bedrooms": 2,
      "price_per_night": 180
    }
  ],
  "org_id": 123 // Your organization ID (scoped data)
}
```

**What happens**:
1. FastAPI validates X-API-Key against Supabase
2. Retrieves org_id from api_keys table
3. Fetches encrypted Hostaway credentials for org_id
4. Decrypts credentials using Supabase Vault
5. Proxies request to Hostaway API with org's credentials
6. Logs invocation to audit_logs table
7. Increments usage_metrics for current month

---

### Example 2: Create Listing

**Claude Desktop prompt**:
> "Create a new 2-bedroom listing in Austin, TX for $150/night"

**MCP invocation**:
```bash
curl -X POST \
  -H "X-API-Key: api_abc123..." \
  https://mcp.hostaway-server.com/api/listings \
  -d '{
    "name": "Austin Bungalow",
    "city": "Austin",
    "bedrooms": 2,
    "price_per_night": 150
  }'
```

**Response**:
```json
{
  "listing_id": 103,
  "status": "created",
  "message": "Listing created successfully. Stripe subscription will update on next daily sync."
}
```

**What happens**:
1. API key validated → org_id resolved
2. Listing created in Hostaway under org's account
3. Next daily sync: Listing count increases (15 → 16)
4. Stripe subscription updated: quantity=16, prorated charge $2.50 (remaining 15 days)

---

## Troubleshooting

### Issue: 401 Unauthorized on MCP Request

**Symptom**: All MCP tools return `{"detail": "Invalid API key"}`

**Solutions**:
1. **Check API key**: Ensure X-API-Key header matches generated key (copy-paste error?)
2. **Key regenerated**: If you regenerated key, old key is invalidated (use new key)
3. **Key deleted**: Verify key still active in dashboard API Keys page
4. **Payment failed**: If subscription past_due, API keys suspended (check Billing page)

```bash
# Test API key validity
curl -H "X-API-Key: your_key_here" https://mcp.hostaway-server.com/api/health
# Expected: {"status": "ok", "org_id": 123}
# If 401: Key invalid or inactive
```

---

### Issue: Listing Count Mismatch

**Symptom**: Dashboard shows 15 listings, Hostaway shows 18

**Solution**:
1. Click **Sync Listing Count** in Billing page
2. System fetches latest count from Hostaway
3. Updates Stripe subscription with proration
4. Refresh dashboard to see updated count

**Prevention**: Automatic daily sync at 2 AM UTC (no action needed)

---

### Issue: Payment Failed / API Keys Suspended

**Symptom**: MCP requests return 401, dashboard shows "Subscription Past Due"

**Flow**:
1. Stripe payment fails → webhook sent to Supabase Edge Function
2. Edge Function sets api_keys.is_active=false for your org
3. Email sent: "Payment failed - please update payment method"
4. MCP requests blocked until payment succeeds

**Solution**:
1. Go to Billing page → Click **Manage in Stripe**
2. Update payment method in Stripe customer portal
3. Retry payment (manual or automatic retry)
4. On success: Webhook restores api_keys.is_active=true
5. MCP requests work again (usually within 5 minutes)

---

### Issue: Cannot Generate 6th API Key

**Symptom**: "Maximum 5 active API keys per organization" error

**Solution**:
1. Go to API Keys page
2. Delete unused or compromised keys
3. Generate new key (now under limit)

**Tip**: Review `last_used_at` to identify inactive keys

---

## Next Steps

1. **Explore MCP Tools**: Use Claude Desktop with your API key to manage properties
2. **Monitor Usage**: Check Usage Metrics page weekly to track costs
3. **Automate Workflows**: Use Claude to batch-update listings, analyze bookings
4. **Add Team Members** (future): Invite users to your organization
5. **API Documentation**: See full MCP tool reference at `/docs`

---

**Quickstart Complete** | v2.0 Multi-Tenant Platform Ready for Use
