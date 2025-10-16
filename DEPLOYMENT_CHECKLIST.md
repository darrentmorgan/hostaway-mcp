# Production Deployment Checklist

## ⚠️ CRITICAL: Pre-Deployment Risks

### Constitution Violations (MUST ACKNOWLEDGE)

**❌ BLOCKER: Test Coverage Below 80%**
- **Current Coverage**: 0% (no tests implemented)
- **Required by**: Constitution Principle IV (TDD)
- **Risk Level**: CRITICAL
- **Impact**: Production bugs, regressions, debugging difficulty
- **Recommendation**: Add tests (T045-T050) before deployment OR document exception

**❌ HIGH: Missing Features**
- Table sorting/pagination (FR-012) not implemented
- Form validation (FR-011) incomplete
- TypeScript strict mode not verified

**Decision Required**:
- [ ] Option A: Delay deployment, add tests (~35 hours)
- [ ] Option B: Deploy with risk acknowledgment + 30-day remediation plan
- [ ] Option C: Deploy to staging only, not production

---

## Phase 1: Code Preparation

### 1.1 Git & Version Control
- [x] Build passes without errors
- [ ] All changes committed to feature branch
- [ ] Feature branch merged to `main` (or deployment branch)
- [ ] Git tags created for version tracking

```bash
# Commit changes
git add .
git commit -m "feat: dashboard implementation with navigation and usage page

- Add breadcrumb navigation
- Add mobile menu with Sheet component
- Implement usage page with metrics and charts
- Add loading and error states

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Merge to main (or create PR)
git checkout main
git merge 004-we-need-to
git push origin main

# Tag release
git tag -a v1.0.0-beta -m "Beta release: Dashboard MVP"
git push origin v1.0.0-beta
```

### 1.2 Environment Variables
- [ ] Production Supabase project created
- [ ] Production Stripe account configured
- [ ] All secrets documented in `.env.production.example`
- [ ] Secrets added to deployment platforms

---

## Phase 2: Supabase Deployment

### 2.1 Create Production Project
```bash
# Login to Supabase
cd ..
supabase login

# Link to production project
supabase link --project-ref your-production-project-ref

# Push migrations
supabase db push

# Verify migrations applied
supabase db diff
```

### 2.2 Configure Supabase
- [ ] Database migrations pushed
- [ ] RLS policies enabled
- [ ] Row Level Security tested
- [ ] Auth providers configured (email, OAuth)
- [ ] Storage buckets created (if needed)
- [ ] Edge Functions deployed (if any)

### 2.3 Get Production Credentials
```bash
# Get project URL and keys
supabase status

# Or from dashboard:
# https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api
```

**Copy these values**:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

### 2.4 Verify Database
```bash
# Test connection
supabase db inspect

# Check tables exist
supabase db execute "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
```

---

## Phase 3: Vercel Deployment

### 3.1 Install Vercel CLI
```bash
npm install -g vercel
vercel login
```

### 3.2 Link Project
```bash
cd dashboard
vercel link
```

### 3.3 Configure Environment Variables

**Via CLI**:
```bash
# Add production environment variables
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add SUPABASE_SERVICE_ROLE_KEY production
vercel env add NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY production
vercel env add STRIPE_SECRET_KEY production
vercel env add NEXT_PUBLIC_APP_URL production
vercel env add NEXT_PUBLIC_API_URL production

# Enable analytics
vercel env add NEXT_PUBLIC_ENABLE_ANALYTICS production
vercel env add NEXT_PUBLIC_ENABLE_SENTRY production
```

**Via Dashboard**:
1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to Settings > Environment Variables
4. Add all variables from `.env.production.example`

### 3.4 Deploy to Production
```bash
# Preview deployment first
vercel

# Deploy to production
vercel --prod

# Or push to main branch (auto-deploy)
git push origin main
```

### 3.5 Verify Deployment
- [ ] Visit production URL
- [ ] Test authentication flow
- [ ] Check usage page loads
- [ ] Verify Supabase connection
- [ ] Test mobile navigation
- [ ] Check breadcrumbs work
- [ ] Monitor Vercel logs for errors

**Check logs**:
```bash
vercel logs --follow
```

---

## Phase 4: Hostinger Deployment (API/Backend)

### 4.1 Prepare API for Production
```bash
cd ../src/api

# Verify dependencies
uv sync --frozen

# Test production build
uv run python -m src.api.main
```

### 4.2 Configure Hostinger

**Option A: Docker Deployment**
```bash
# Build production image
docker build -t hostaway-mcp-api:latest -f Dockerfile .

# Test locally
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SUPABASE_URL="https://..." \
  hostaway-mcp-api:latest

# Push to registry (Docker Hub, GitHub Container Registry, etc.)
docker tag hostaway-mcp-api:latest your-registry/hostaway-mcp-api:latest
docker push your-registry/hostaway-mcp-api:latest
```

**Option B: Direct Deployment**
1. SSH into Hostinger server
2. Clone repository
3. Install dependencies with `uv`
4. Configure systemd service
5. Set up Nginx reverse proxy

### 4.3 Hostinger Environment Variables
Create `.env` on server:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_key
HOSTAWAY_ACCOUNT_ID=your_account
HOSTAWAY_SECRET_KEY=your_secret
PORT=8000
```

### 4.4 Configure Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 4.5 SSL Certificate
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d api.your-domain.com
```

---

## Phase 5: Post-Deployment Verification

### 5.1 Smoke Tests
- [ ] Homepage loads
- [ ] Login works
- [ ] Signup works
- [ ] Usage page displays data
- [ ] API connection works
- [ ] Stripe integration works (test mode first)
- [ ] Mobile menu works
- [ ] Breadcrumbs display correctly

### 5.2 Security Checks
- [ ] HTTPS enabled (SSL certificates valid)
- [ ] RLS policies working in Supabase
- [ ] API keys not exposed in client
- [ ] CORS configured correctly
- [ ] Rate limiting enabled (if configured)

### 5.3 Performance Checks
```bash
# Run Lighthouse audit
npx lighthouse https://your-dashboard.vercel.app --view

# Check bundle size
cd dashboard
npm run build
du -sh .next
```

- [ ] Lighthouse Performance > 90
- [ ] Time to Interactive < 3s
- [ ] First Contentful Paint < 1.5s
- [ ] No console errors

### 5.4 Monitoring Setup
- [ ] Vercel Analytics enabled
- [ ] Supabase logs configured
- [ ] Error tracking (Sentry) configured
- [ ] Uptime monitoring (if using)

---

## Phase 6: Rollback Plan

### If Issues Arise:

**Vercel Rollback**:
```bash
# List deployments
vercel ls

# Rollback to previous
vercel rollback [deployment-url]
```

**Supabase Rollback**:
```bash
# Revert migration
supabase migration repair <version> --status reverted
supabase db reset
```

**Emergency Contact**:
- Vercel Support: https://vercel.com/support
- Supabase Support: https://supabase.com/support
- Hostinger Support: https://www.hostinger.com/contact

---

## Production URLs (Update After Deployment)

- **Dashboard**: https://_____.vercel.app
- **API**: https://api._____.hostinger.com
- **Supabase**: https://_____.supabase.co
- **Supabase Studio**: https://supabase.com/dashboard/project/_____

---

## Post-Deployment TODO

### Within 7 Days:
- [ ] Monitor error rates in Vercel
- [ ] Check Supabase usage metrics
- [ ] Review API logs for issues
- [ ] Gather initial user feedback

### Within 30 Days (If Option B chosen):
- [ ] Add test coverage (T045-T050)
- [ ] Implement table sorting/pagination
- [ ] Complete form validation
- [ ] Verify TypeScript strict mode
- [ ] Reach >80% test coverage

---

## Support & Documentation

- **Next.js Docs**: https://nextjs.org/docs
- **Vercel Docs**: https://vercel.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Turbopack**: https://turbo.build/pack/docs
