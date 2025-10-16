# API Key Management - Quick Start Guide

## Prerequisites
- ✅ Supabase project with `api_keys` table created
- ✅ User authentication working (Supabase Auth)
- ✅ Organization membership setup
- ✅ Dashboard running on `localhost:3000` (or configured port)

## Installation

Already completed in this implementation:

```bash
# Navigate to dashboard directory
cd /Users/darrenmorgan/AI_Projects/hostaway-mcp/dashboard

# Install dependencies (already done)
npm install

# Dependency added: @headlessui/react@^2.2.9
```

## Files Created

```
✅ /dashboard/app/(dashboard)/api-keys/page.tsx
✅ /dashboard/app/(dashboard)/api-keys/actions.ts
✅ /dashboard/components/api-keys/APIKeyList.tsx
✅ /dashboard/components/api-keys/APIKeyGenerateModal.tsx
✅ /dashboard/components/api-keys/APIKeyDisplay.tsx
```

## Running the Feature

### 1. Start Development Server

```bash
cd /Users/darrenmorgan/AI_Projects/hostaway-mcp/dashboard
npm run dev
```

### 2. Access the Page

Navigate to: `http://localhost:3000/api-keys`

(You must be logged in with a user that belongs to an organization)

### 3. Generate Your First API Key

1. Click the "Generate New Key" button
2. Read the security warning
3. Click "Generate Key"
4. Copy the displayed API key (format: `mcp_xxxxx...`)
5. Save it securely (you won't see it again!)
6. Click "I've saved my key"

## Quick Testing

### Happy Path Test
```
1. Navigate to /api-keys
2. Generate a new key
3. Copy the key to clipboard
4. Verify key appears in list as "Active"
5. Try regenerating the key
6. Verify old key becomes "Inactive"
7. Try deleting a key
8. Verify key status changes to "Inactive"
```

### Edge Case Test
```
1. Generate 5 API keys
2. Verify warning appears: "Maximum limit reached"
3. Verify "Generate New Key" button is disabled
4. Delete one key
5. Verify button becomes enabled again
6. Generate a new key successfully
```

## Using the API Key

### In Claude Desktop Config

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hostaway": {
      "url": "http://localhost:3000/api/mcp",
      "headers": {
        "X-API-Key": "mcp_your_generated_key_here"
      }
    }
  }
}
```

### Testing API Key Validation

```bash
# Test with curl
curl -H "X-API-Key: mcp_your_key_here" \
  http://localhost:3000/api/mcp/validate

# Should return:
# { "valid": true, "organization_id": 123 }
```

## Common Issues & Solutions

### Issue: Page not accessible
**Solution:** Ensure you're logged in and have organization membership

### Issue: "Not authenticated" error
**Solution:**
```bash
# Check if user session is valid
# Navigate to /login and log in again
```

### Issue: Can't generate keys
**Solution:**
```sql
-- Verify api_keys table exists in Supabase
SELECT * FROM api_keys LIMIT 1;

-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename = 'api_keys';
```

### Issue: Copy button doesn't work
**Solution:**
- Use HTTPS or localhost (clipboard API requirement)
- Check browser console for errors
- Try a different browser

## API Key Format

```
Format: mcp_<32 random characters>
Example: mcp_a7b2c9d4e1f8g3h6i5j2k9l4m7n0p3q6

✅ Valid: mcp_aBcD1234eFgH5678iJkL9012mNoPqRsT
❌ Invalid: mcp_short
❌ Invalid: api_key_123456
```

## Database Verification

### Check Keys in Database

```sql
-- View all API keys for your organization
SELECT
  id,
  LEFT(key_hash, 10) || '...' as key_hash_preview,
  is_active,
  created_at,
  last_used_at
FROM api_keys
WHERE organization_id = YOUR_ORG_ID
ORDER BY created_at DESC;
```

### Verify Key Hash Format

```sql
-- Should return 64 (SHA-256 produces 64 hex characters)
SELECT LENGTH(key_hash) as hash_length
FROM api_keys
LIMIT 1;
```

## Security Checklist

Before deploying to production:

- [ ] Verify all API keys are hashed (64 hex characters)
- [ ] Confirm no full keys in database
- [ ] Check no keys in application logs
- [ ] Verify RLS policies are active
- [ ] Test key validation in MCP server
- [ ] Confirm HTTPS is enabled
- [ ] Review error messages (no sensitive data leaked)
- [ ] Test rate limiting (5 keys max)

## Environment Variables

Required in `.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Development Tips

### Watch for Changes

```bash
# Terminal 1: Run dev server
npm run dev

# Terminal 2: Watch TypeScript errors
npx tsc --noEmit --watch
```

### Check Component Props

```typescript
// APIKeyList.tsx
interface APIKeyListProps {
  keys: ApiKey[]           // Array of API key objects
  maxKeysReached: boolean  // True when 5 active keys exist
}

// APIKeyGenerateModal.tsx
interface APIKeyGenerateModalProps {
  isOpen: boolean
  onClose: () => void
  onGenerate: () => Promise<{ success: boolean; apiKey?: string; error?: string }>
}
```

### Debug Server Actions

```typescript
// Add console.log in actions.ts
export async function generateApiKey() {
  console.log('🔑 Generating API key...')
  // ... rest of code
  console.log('✅ API key generated successfully')
}
```

## Next Steps

1. **Test thoroughly** - Use `/API_KEYS_TESTING_GUIDE.md`
2. **Review security** - Audit all code paths
3. **Update MCP server** - Implement key validation
4. **Write docs** - User-facing documentation
5. **Deploy to staging** - Test in production-like environment

## Support

### Documentation
- Implementation details: `/API_KEYS_IMPLEMENTATION_SUMMARY.md`
- Testing checklist: `/API_KEYS_TESTING_GUIDE.md`
- This guide: `/API_KEYS_QUICKSTART.md`

### Code Locations
- Server Components: `/dashboard/app/(dashboard)/api-keys/`
- Client Components: `/dashboard/components/api-keys/`
- Types: `/dashboard/lib/types/database.ts`

### Useful Commands

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint

# Type check
npx tsc --noEmit

# Check for unused dependencies
npm prune
```

## Feature Flags (Optional)

If you want to enable/disable the feature:

```typescript
// In page.tsx, add at the top
const FEATURE_API_KEYS_ENABLED = process.env.NEXT_PUBLIC_FEATURE_API_KEYS === 'true'

if (!FEATURE_API_KEYS_ENABLED) {
  redirect('/dashboard')
}
```

Then in `.env.local`:
```bash
NEXT_PUBLIC_FEATURE_API_KEYS=true
```

---

**Ready to test!** Navigate to `/api-keys` and start generating API keys.

For detailed testing procedures, see `/API_KEYS_TESTING_GUIDE.md`
