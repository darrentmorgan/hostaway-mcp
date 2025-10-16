# Hostaway MCP - Multi-Tenant SaaS Quickstart

**Get started with Hostaway MCP in 5 minutes**

This guide walks you through onboarding, connecting your Hostaway account, and using MCP tools with Claude Desktop.

---

## Production URLs

- **Dashboard**: https://dashboard.hostaway-mcp.com (Vercel deployment - TBD)
- **Backend API**: https://api.hostaway-mcp.com (VPS deployment - TBD)
- **Stripe Portal**: https://billing.stripe.com/p/login/test_xxx (TBD)

> **Note**: URLs marked TBD will be updated after Phase 8 deployment (T065-T067)

---

## For End Users

### Step 1: Sign Up

1. Visit https://dashboard.hostaway-mcp.com
2. Click "Sign up with email"
3. Enter your email and create a password
4. Check your email for the verification link
5. Click the verification link to activate your account

### Step 2: Connect Your Hostaway Account

1. Log in to the dashboard
2. Go to "Settings" page
3. In the "Hostaway Integration" section, enter:
   - **Account ID**: Your Hostaway account ID
   - **API Key**: Your Hostaway API key
   - **Account Secret**: Your Hostaway secret key
4. Click "Save Credentials"
5. Test connection with "Test Connection" button

> **Where to find Hostaway credentials**:
> - Log in to Hostaway Dashboard
> - Go to Settings ’ API Access
> - Create new API credentials if needed

### Step 3: Start Your Subscription

1. Navigate to "Billing" page
2. You'll see a prompt to start your subscription
3. Click "Start Subscription"
4. Enter payment details (Stripe checkout)
5. Your subscription will be based on your active listings count
6. **Pricing**: $5/listing/month

### Step 4: Generate Your MCP API Key

1. Go to "API Keys" page
2. Click "Create New API Key"
3. Give it a descriptive name (e.g., "Claude Desktop - MacBook")
4. Click "Create"
5. **Important**: Copy the API key immediately - it won't be shown again!
6. Store it securely (e.g., password manager)

### Step 5: Configure Claude Desktop

1. Open Claude Desktop application
2. Go to Settings ’ Developer ’ MCP Settings
3. Click "Edit Config" (opens `claude_desktop_config.json`)
4. Add this configuration:

```json
{
  "mcpServers": {
    "hostaway-mcp": {
      "url": "https://api.hostaway-mcp.com/mcp",
      "headers": {
        "X-API-Key": "your_api_key_from_step_4"
      },
      "description": "Hostaway property management tools"
    }
  }
}
```

5. Save the file and restart Claude Desktop

### Step 6: Verify Connection

1. In Claude Desktop, check Settings ’ Developer ’ MCP Servers
2. You should see "hostaway-mcp" with a green "Connected" status
3. Test it by asking Claude: *"Use Hostaway MCP to list my properties"*

**Available MCP Tools**:
- `get_listings` - Retrieve all property listings
- `get_listing` - Get details for a specific listing
- `get_listing_availability` - Check availability calendar
- `get_bookings` - List bookings
- `get_booking` - Get booking details
- `create_listing` - Create new property listing
- `batch_update_listings` - Update multiple listings at once
- `get_financial_summary` - Analyze revenue and booking metrics

---

## For Administrators

### Deployment Overview

The Hostaway MCP platform consists of 3 main components:

1. **Supabase Database** (managed by Supabase)
   - PostgreSQL with Row Level Security (RLS)
   - Authentication and user management
   - Stores: organizations, credentials, API keys, subscriptions, usage metrics

2. **Next.js Dashboard** (deployed on Vercel)
   - React frontend with Server Components
   - Stripe billing integration
   - User authentication via Supabase Auth

3. **FastAPI Backend** (deployed on VPS)
   - Python REST API with MCP integration
   - Hostaway API client
   - Rate limiting and usage tracking

### Environment Setup

#### Backend (.env)

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_key

# Rate Limiting
RATE_LIMIT_IP=100
RATE_LIMIT_ACCOUNT=1000
MAX_CONCURRENT_REQUESTS=50

# API Security
API_KEY_SECRET=your_random_32_char_secret

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=production
```

#### Dashboard (.env.local)

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key

# Stripe
STRIPE_SECRET_KEY=sk_live_xxx
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_ID=price_xxx

# URLs
NEXT_PUBLIC_APP_URL=https://dashboard.hostaway-mcp.com
NEXT_PUBLIC_API_URL=https://api.hostaway-mcp.com

NODE_ENV=production
```

### Deployment Steps

#### 1. Deploy Supabase Database (T064)

```bash
# From project root
supabase db push

# Verify migrations applied
supabase db migrations list
```

#### 2. Deploy Next.js Dashboard (T065)

```bash
# Connect to Vercel (first time only)
cd dashboard
vercel link

# Deploy to production
vercel --prod

# Configure environment variables in Vercel dashboard
# (All NEXT_PUBLIC_* and Stripe secrets)
```

#### 3. Deploy Supabase Edge Functions (T066)

```bash
# Deploy all edge functions
supabase functions deploy

# Or deploy individually
supabase functions deploy sync-stripe-listings
```

#### 4. Deploy FastAPI Backend (T067)

```bash
# Transfer files to VPS
rsync -avz --exclude '.venv' --exclude 'logs' \
  . root@your-vps:/opt/hostaway-mcp/

# SSH into VPS
ssh root@your-vps

# Install dependencies
cd /opt/hostaway-mcp
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Configure systemd service
sudo cp deploy/hostaway-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hostaway-mcp
sudo systemctl start hostaway-mcp

# Verify
curl http://localhost:8000/health
```

#### 5. Configure Stripe Webhooks (T068)

1. Go to Stripe Dashboard ’ Developers ’ Webhooks
2. Click "Add endpoint"
3. **Endpoint URL**: `https://api.hostaway-mcp.com/webhooks/stripe`
4. **Events to send**:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
5. Copy the webhook signing secret to `.env` as `STRIPE_WEBHOOK_SECRET`

#### 6. Test End-to-End (T069)

1. Sign up with a test email
2. Connect Hostaway credentials
3. Start Stripe subscription (test mode)
4. Generate MCP API key
5. Configure Claude Desktop
6. Test MCP tools

#### 7. Verify Multi-Tenant Isolation (T070)

1. Create 2 test accounts (User A, User B)
2. User A connects Hostaway account X
3. User B connects Hostaway account Y
4. Verify User A cannot see User B's listings
5. Verify API key from User A fails for User B's data
6. Check Supabase RLS policies are enforced

---

## Monitoring & Maintenance

### Health Checks

- **Backend**: `curl https://api.hostaway-mcp.com/health`
- **Dashboard**: `curl https://dashboard.hostaway-mcp.com/api/health`

### Usage Metrics

View usage metrics in the dashboard "Usage" page:
- Total API requests (current month)
- Active listings count
- Projected monthly bill
- Unique tools used
- 30-day request volume chart

### Invoice History

View billing history in the "Billing" page:
- Past invoices with PDF downloads
- Payment status
- Listing count per billing period
- Stripe customer portal link

### Logs

- **Backend logs**: `journalctl -u hostaway-mcp -f` (on VPS)
- **Dashboard logs**: Vercel dashboard ’ Logs tab
- **Supabase logs**: Supabase dashboard ’ Logs

---

## Troubleshooting

### User Can't Sign Up

**Symptoms**: Email verification link doesn't work

**Fix**:
1. Check Supabase Auth settings
2. Verify email provider is configured
3. Check spam/junk folders
4. Use magic link login as alternative

### Hostaway Connection Fails

**Symptoms**: "Invalid credentials" or "Connection failed" error

**Fix**:
1. Verify credentials in Hostaway dashboard
2. Check API key hasn't expired
3. Test credentials directly with Hostaway API:
   ```bash
   curl -X POST https://api.hostaway.com/v1/accessTokens \
     -d "grant_type=client_credentials" \
     -d "client_id=YOUR_ACCOUNT_ID" \
     -d "client_secret=YOUR_SECRET"
   ```

### Stripe Subscription Fails

**Symptoms**: Payment declined or subscription not activated

**Fix**:
1. Use test card: `4242 4242 4242 4242` (test mode)
2. Check Stripe dashboard for failed payments
3. Verify webhook endpoint is receiving events
4. Review backend logs for webhook processing errors

### MCP Tools Not Working

**Symptoms**: Claude Desktop shows "hostaway-mcp" disconnected

**Fix**:
1. Check API key is valid: Go to dashboard ’ API Keys
2. Verify backend is running: `curl https://api.hostaway-mcp.com/health`
3. Test MCP endpoint with curl:
   ```bash
   curl https://api.hostaway-mcp.com/mcp \
     -H "X-API-Key: your_api_key"
   ```
4. Restart Claude Desktop
5. Check Claude Desktop logs: `~/Library/Logs/Claude/`

### Multi-Tenant Isolation Issues

**Symptoms**: User can see another organization's data

**Fix**:
1. **CRITICAL SECURITY ISSUE** - investigate immediately
2. Check RLS policies in Supabase:
   ```sql
   SELECT * FROM organizations WHERE id = 'other_org_id';
   -- Should return empty or access denied
   ```
3. Review API key ’ organization mapping in database
4. Check all FastAPI endpoints use `get_organization_context()` dependency

---

## Support

- **Documentation**: See `/docs` folder
- **Issues**: GitHub Issues (TBD)
- **Email**: support@hostaway-mcp.com (TBD)

---

**Ready to integrate Hostaway with Claude AI!** =€
