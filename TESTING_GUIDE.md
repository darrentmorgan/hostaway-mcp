# Hostaway MCP Server - Testing Guide

**Status**: Phases 1-4 Complete (33/70 tasks)
**Date**: October 13, 2025

## 🚀 Currently Running Services

| Service | URL | Status |
|---------|-----|--------|
| **FastAPI Backend** | http://localhost:8000 | ✅ Running |
| **Next.js Dashboard** | http://localhost:3001 | ✅ Running |
| **Supabase Local** | http://127.0.0.1:54321 | ✅ Running |
| **Supabase Studio** | http://127.0.0.1:54323 | ✅ Available |

---

## 📋 Test Checklist - Full Flow

### Phase 1: User Signup & Organization Creation

**Test: New User Registration**

1. **Navigate to Signup**:
   ```
   http://localhost:3001/signup
   ```

2. **Create Test Account**:
   - Email: `test@example.com`
   - Password: `Password123!` (minimum 8 characters)
   - Confirm Password: `Password123!`

3. **Click "Sign up"**

4. **Expected Behavior**:
   - ✅ Success message displayed
   - ✅ Organization automatically created
   - ✅ Redirects to `/login` after 2 seconds

5. **Verify in Supabase**:
   - Open Supabase Studio: http://127.0.0.1:54323
   - Check `auth.users` table - user should exist
   - Check `organizations` table - organization created
   - Check `organization_members` table - member record with role='owner'

---

### Phase 2: User Login

**Test: Authentication**

1. **Navigate to Login**:
   ```
   http://localhost:3001/login
   ```

2. **Login with Test Account**:
   - Email: `test@example.com`
   - Password: `Password123!`

3. **Click "Sign in"**

4. **Expected Behavior**:
   - ✅ Successful authentication
   - ✅ Redirects to `/dashboard` or `/settings`
   - ✅ Navigation bar shows email and role badge
   - ✅ "Sign Out" button visible

---

### Phase 3: Hostaway Credentials Connection

**Test: Connect Hostaway Account**

1. **Navigate to Settings**:
   ```
   http://localhost:3001/settings
   ```

2. **Enter Hostaway Credentials**:
   - Account ID: `161051` (from your .env)
   - Secret Key: `***REMOVED***` (from your .env)

3. **Click "Connect Hostaway"**

4. **Expected Behavior**:
   - ✅ "Validating credentials..." loading state
   - ✅ **Live API call to Hostaway** to validate credentials
   - ✅ Success message: "Hostaway credentials connected successfully!"
   - ✅ Status changes to "Connected" with green badge
   - ✅ Shows "Last validated" timestamp

5. **Verify in Supabase**:
   - Check `hostaway_credentials` table:
     - `account_id`: `161051` (plain text)
     - `encrypted_secret_key`: Base64 encrypted string
     - `credentials_valid`: `true`
     - `last_validated_at`: Recent timestamp

**Note**: If you get a 401 error, the Hostaway credentials are invalid/expired. Use valid credentials from your Hostaway account.

---

### Phase 4: API Key Management

**Test: Generate API Key**

1. **Navigate to API Keys**:
   ```
   http://localhost:3001/api-keys
   ```

2. **Click "Generate New Key"**

3. **Expected Behavior**:
   - ✅ Modal opens with "Generating..." state
   - ✅ Random API key generated: `mcp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (32 chars after prefix)
   - ✅ Full key displayed ONCE with copy button
   - ✅ Security warning: "This is the only time you'll see this key"
   - ✅ Copy button works (shows checkmark after copy)

4. **Copy the API Key** (you'll need this for MCP testing)

5. **Click "Close"**

6. **Expected Behavior**:
   - ✅ Modal closes
   - ✅ New key appears in list (masked: `abc123...xyz789`)
   - ✅ Shows "Never used" for last_used_at
   - ✅ Status badge: "Active" (green)
   - ✅ "Regenerate" and "Delete" buttons available

**Test: API Key Limit**

7. **Generate 4 more API keys** (total 5)

8. **Try to generate a 6th key**

9. **Expected Behavior**:
   - ✅ Error message: "Maximum of 5 API keys reached"
   - ✅ "Generate New Key" button disabled
   - ✅ Warning message shows max limit

**Test: Delete API Key**

10. **Click "Delete" on one key**

11. **Confirm deletion**

12. **Expected Behavior**:
    - ✅ Key status changes to "Inactive" (gray badge)
    - ✅ Key remains in list (soft delete)
    - ✅ Can now generate new keys (below 5 limit)

**Test: Regenerate API Key**

13. **Click "Regenerate" on an active key**

14. **Confirm regeneration**

15. **Expected Behavior**:
    - ✅ Old key marked as inactive
    - ✅ New key generated and displayed
    - ✅ Must copy new key before closing

---

### Phase 5: FastAPI Backend Testing

**Test: API Key Authentication**

1. **Copy an active API key** from the dashboard

2. **Test with curl**:
   ```bash
   # Replace YOUR_API_KEY with your actual key
   curl -X GET http://localhost:8000/health \
     -H "X-API-Key: YOUR_API_KEY" \
     -H "Content-Type: application/json"
   ```

3. **Expected Response** (without API key):
   ```json
   {
     "status": "healthy",
     "version": "0.1.0",
     "timestamp": "2025-10-13T..."
   }
   ```

**Test: Organization Context Dependency**

4. **Test a protected endpoint** (once you have one):
   ```bash
   curl -X GET http://localhost:8000/api/properties \
     -H "X-API-Key: YOUR_API_KEY" \
     -H "Content-Type: application/json"
   ```

5. **Expected Behavior**:
   - ✅ API key validated (SHA-256 hash lookup)
   - ✅ Organization ID retrieved
   - ✅ Hostaway credentials decrypted
   - ✅ `credentials_valid` flag checked
   - ✅ `last_used_at` updated in database

6. **Test Invalid API Key**:
   ```bash
   curl -X GET http://localhost:8000/api/properties \
     -H "X-API-Key: invalid_key_123" \
     -H "Content-Type: application/json"
   ```

7. **Expected Response**:
   ```json
   {
     "detail": "Invalid or inactive API key"
   }
   ```

---

## 🔍 Database Verification

### Check Data via Supabase Studio

1. **Open Supabase Studio**: http://127.0.0.1:54323

2. **Verify Tables**:

**auth.users** - Supabase Auth Users
```sql
SELECT id, email, created_at FROM auth.users;
```

**organizations** - Your Organizations
```sql
SELECT id, name, owner_user_id, stripe_customer_id, created_at
FROM organizations;
```

**organization_members** - Membership
```sql
SELECT om.id, om.organization_id, om.user_id, om.role, o.name as org_name
FROM organization_members om
JOIN organizations o ON o.id = om.organization_id;
```

**hostaway_credentials** - Encrypted Credentials
```sql
SELECT id, organization_id, account_id,
       LEFT(encrypted_secret_key, 20) as encrypted_key_preview,
       credentials_valid, last_validated_at
FROM hostaway_credentials;
```

**api_keys** - MCP API Keys
```sql
SELECT id, organization_id,
       LEFT(key_hash, 12) as hash_preview,
       is_active, last_used_at, created_at
FROM api_keys
ORDER BY created_at DESC;
```

### Check RLS Policies

**Test Row Level Security**:

1. **Create 2nd user** with different email

2. **Verify isolation**:
   - User A cannot see User B's organizations
   - User A cannot see User B's API keys
   - User A cannot access User B's Hostaway credentials

---

## 🧪 Advanced Testing

### Test Multi-Tenancy

1. **Create 2 separate organizations**:
   - User A: `usera@example.com`
   - User B: `userb@example.com`

2. **Connect different Hostaway accounts** (if available)

3. **Generate API keys for each**

4. **Verify data isolation**:
   ```bash
   # User A's API key should only access User A's data
   curl -X GET http://localhost:8000/api/properties \
     -H "X-API-Key: user_a_api_key"

   # User B's API key should only access User B's data
   curl -X GET http://localhost:8000/api/properties \
     -H "X-API-Key: user_b_api_key"
   ```

### Test Encryption

**Verify Secret Key Encryption**:

1. **Check encrypted value in database**:
   ```sql
   SELECT encrypted_secret_key FROM hostaway_credentials LIMIT 1;
   ```

2. **Should be Base64 string** (not plain text)

3. **Test decryption** (happens automatically in API):
   - Decryption uses `decrypt_hostaway_credential` RPC function
   - Uses vault encryption key from `vault.secrets`
   - Only accessible with service role key

---

## 🐛 Troubleshooting

### Common Issues

**1. "Email already exists" on signup**
- Solution: Use different email OR delete user from `auth.users` table

**2. Hostaway credentials validation fails**
- Check credentials are valid on https://dashboard.hostaway.com
- Verify API key has proper permissions
- Check error message for specific issue (401 = invalid, network errors, etc.)

**3. API key not working**
- Verify key is active in dashboard
- Check you're using full key (not masked version)
- Confirm `X-API-Key` header is set correctly

**4. "Maximum 5 API keys" when you have less**
- Query shows only active keys
- Check `api_keys` table for `is_active = false` records
- Delete inactive keys if needed

**5. Next.js port 3001 instead of 3000**
- Port 3000 is in use by another process
- Use http://localhost:3001 instead
- Or kill process on 3000: `lsof -ti:3000 | xargs kill`

**6. "Hostaway credentials not configured"**
- Complete Phase 3 (connect Hostaway account) first
- Verify `hostaway_credentials` record exists in database

---

## 📊 Success Metrics

### ✅ All Tests Passing

After completing all tests, you should have:

- [x] User can signup → organization created
- [x] User can login → session active
- [x] User can connect Hostaway credentials (validated via API)
- [x] User can generate up to 5 API keys
- [x] User can copy, regenerate, and delete API keys
- [x] API keys authenticate FastAPI requests
- [x] Organization context provides decrypted Hostaway credentials
- [x] Multi-tenant isolation via RLS policies
- [x] Encryption working for secret keys

---

## 🚀 Next Steps

After successful testing:

1. **Deploy to Hostinger VPS**:
   ```bash
   ./scripts/deploy.sh production
   ```

2. **Or use GitHub Actions**:
   - Push to `main` or `production` branch
   - CI/CD automatically deploys

3. **Continue Implementation**:
   - Phase 5: Stripe Billing (11 tasks)
   - Phase 6: Usage Metrics (7 tasks)
   - Phase 7: AI Operations (6 tasks)
   - Phase 8: Production Polish (12 tasks)

---

## 📝 Test Results Template

```
# Test Session: October 13, 2025

## Environment
- FastAPI: http://localhost:8000 ✅
- Next.js: http://localhost:3001 ✅
- Supabase: http://127.0.0.1:54321 ✅

## Phase 1: Signup (T018-T020)
- [ ] User signup works
- [ ] Organization created
- [ ] Member record created
- [ ] Redirects to login

## Phase 2: Login (T019, T024)
- [ ] User can login
- [ ] Dashboard accessible
- [ ] Auth guard works
- [ ] Navigation displays user info

## Phase 3: Hostaway (T021-T022, T025)
- [ ] Credentials form displays
- [ ] API validation works
- [ ] Encrypted and stored
- [ ] FastAPI can decrypt

## Phase 4: API Keys (T026-T033)
- [ ] Can generate keys
- [ ] Keys are masked
- [ ] Copy to clipboard works
- [ ] Max 5 limit enforced
- [ ] Delete works (soft delete)
- [ ] Regenerate works
- [ ] FastAPI authentication works
- [ ] last_used_at updates

## Issues Found
- None

## Notes
- All tests passed successfully
```

---

**Happy Testing!** 🎉
