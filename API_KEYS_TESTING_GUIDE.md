# API Key Management - Testing Guide

## Overview
This guide covers testing the API Key Management feature (User Story 2, Tasks T026-T033).

## Implemented Files

### Backend (Server-side)
- `/dashboard/app/(dashboard)/api-keys/page.tsx` - Server Component for API keys page
- `/dashboard/app/(dashboard)/api-keys/actions.ts` - Server Actions for CRUD operations

### Frontend (Client-side)
- `/dashboard/components/api-keys/APIKeyList.tsx` - List display and actions
- `/dashboard/components/api-keys/APIKeyGenerateModal.tsx` - Modal for generation
- `/dashboard/components/api-keys/APIKeyDisplay.tsx` - Display with copy functionality

## Features Implemented

### T026 - API Keys Management Page
- **Route:** `/api-keys`
- **Authentication:** Required (redirects to `/login` if not authenticated)
- **Features:**
  - Displays all API keys (active and inactive) for user's organization
  - Shows warning when 5 active keys limit reached
  - Security best practices notice
  - Sorted by creation date (newest first)

### T027 - Generate API Key Server Action
- **Function:** `generateApiKey()`
- **Security:**
  - Generates secure random API key: `mcp_<32 random chars>`
  - Uses `crypto.randomBytes(24)` for randomness
  - SHA-256 hash stored in database (never the full key)
- **Validation:**
  - Checks user authentication
  - Verifies organization membership
  - Enforces 5 active keys limit per organization
- **Returns:** Full API key (shown once) or error message

### T028 - Delete API Key Server Action
- **Function:** `deleteApiKey(keyId: number)`
- **Security:**
  - Verifies key belongs to user's organization
  - Soft delete (sets `is_active = false`)
- **Confirmation:** Browser confirmation dialog before deletion

### T029 - Regenerate API Key Server Action
- **Function:** `regenerateApiKey(keyId: number)`
- **Process:**
  1. Marks old key as inactive
  2. Generates new random key
  3. Returns new full key (shown once)
- **Confirmation:** Browser confirmation dialog before regeneration

### T030 - APIKeyList Component
- **Display Features:**
  - Masked key hash: First 6 chars + "..." + last 6 chars
  - Created date (formatted)
  - Last used date (or "Never used")
  - Status badge (Active/Inactive)
  - Empty state with helpful message
- **Actions:**
  - Generate New Key button
  - Regenerate button (per active key)
  - Delete button (per active key)
  - Loading states for async operations

### T031 - APIKeyGenerateModal Component
- **States:**
  - Initial: Shows warning, Generate button
  - Generating: Loading spinner
  - Success: Shows full API key with copy button
  - Error: Shows error message
- **Security:**
  - Forces user acknowledgment ("I've saved my key" button)
  - Cannot be accidentally closed (must click button)

### T032 - APIKeyDisplay Component
- **Features:**
  - Monospace code block display
  - Copy to clipboard button with visual feedback
  - Shows checkmark for 2 seconds after copy
  - Security warning: "This is the only time you'll see this key"

### T033 - Max 5 Keys Validation
- **Implementation:**
  - Checked in `generateApiKey()` Server Action
  - Counts active keys before insertion
  - Returns error if limit reached
  - UI shows warning banner when at limit
  - Generate button disabled when at limit

## Testing Checklist

### Setup
- [ ] Database has `api_keys` table with correct schema
- [ ] User is authenticated and has organization membership
- [ ] Navigate to `/api-keys` page

### Generate API Key (Happy Path)
- [ ] Click "Generate New Key" button
- [ ] Modal opens with warning message
- [ ] Click "Generate Key" button
- [ ] Loading spinner appears
- [ ] Success state shows full API key in monospace font
- [ ] API key format: `mcp_<32 random characters>`
- [ ] Copy button works and shows checkmark
- [ ] Security warning is visible
- [ ] Click "I've saved my key" button
- [ ] Modal closes
- [ ] New key appears in the list
- [ ] New key shows as "Active"
- [ ] Last used shows "Never used"

### API Key List Display
- [ ] Keys are sorted by creation date (newest first)
- [ ] Key hash is masked (first 6 + "..." + last 6)
- [ ] Created date is formatted correctly
- [ ] Active keys show green "Active" badge
- [ ] Inactive keys show gray "Inactive" badge
- [ ] Active keys have Regenerate and Delete buttons
- [ ] Inactive keys do not have action buttons

### Delete API Key
- [ ] Click Delete button on an active key
- [ ] Confirmation dialog appears
- [ ] Confirm deletion
- [ ] Loading state appears on button
- [ ] Key status changes to "Inactive"
- [ ] Action buttons disappear for that key
- [ ] Page updates without full refresh

### Regenerate API Key
- [ ] Click Regenerate button on an active key
- [ ] Confirmation dialog appears
- [ ] Confirm regeneration
- [ ] Modal opens showing generation progress
- [ ] New API key is displayed
- [ ] New API key is different from old one
- [ ] Copy button works for new key
- [ ] Close modal
- [ ] Old key is marked as Inactive
- [ ] New key appears in list as Active

### 5 Keys Limit (Edge Case)
- [ ] Generate 5 active API keys
- [ ] Warning banner appears: "Maximum limit reached..."
- [ ] Generate button becomes disabled and grayed out
- [ ] Hover shows cursor-not-allowed
- [ ] Delete one active key
- [ ] Warning banner disappears
- [ ] Generate button becomes enabled again
- [ ] Can generate new key successfully

### Error Handling
- [ ] Try generating key when not authenticated → redirects to login
- [ ] Try accessing page without organization → redirects to login
- [ ] Try deleting key from another organization → shows error message
- [ ] Database error during generation → shows error in modal
- [ ] Network error → shows appropriate error message

### Security Verification
- [ ] Inspect database: only key hash is stored (64 hex characters)
- [ ] Full API key is never logged in console
- [ ] API key shown only once during generation
- [ ] Cannot retrieve full key after modal closes
- [ ] Inactive keys cannot be used for authentication (verify in MCP server)

### Accessibility
- [ ] Keyboard navigation works throughout
- [ ] Focus states visible on all interactive elements
- [ ] Screen reader announces button states
- [ ] Color contrast meets WCAG AA standards
- [ ] Error messages are announced

### Responsive Design
- [ ] Layout works on mobile (320px width)
- [ ] Layout works on tablet (768px width)
- [ ] Layout works on desktop (1280px+ width)
- [ ] Buttons stack properly on small screens
- [ ] Modal is scrollable on small screens
- [ ] Code block doesn't overflow

### Performance
- [ ] Page loads in < 3 seconds
- [ ] No layout shift during key list load
- [ ] Smooth transitions for modal open/close
- [ ] No unnecessary re-renders
- [ ] Copy to clipboard responds instantly

## Known Limitations

1. **One-time Display:** API keys are shown only once. If user closes modal without copying, they must regenerate.
2. **Soft Delete:** Deleted keys remain in database with `is_active = false` for audit trail.
3. **No Edit:** Keys cannot be edited, only regenerated or deleted.
4. **Browser Clipboard:** Copy functionality requires HTTPS in production.

## Integration Points

### Database
- Table: `api_keys`
- Functions used:
  - Standard CRUD via Supabase client
  - `update_api_key_last_used()` (called by MCP server, not dashboard)

### Authentication
- Uses Supabase Auth via Server Components
- Checks `organization_members` table for org membership
- Server Actions verify auth on every request

### MCP Server Integration
- Generated API keys will be used in Claude Desktop config
- MCP server validates keys using `get_organization_by_api_key()` function
- Format: `X-API-Key: mcp_xxxxxxxxxxxxx` header

## Troubleshooting

### Issue: "Not authenticated" error
**Solution:** Ensure user is logged in and has valid session

### Issue: "No organization found" error
**Solution:** User must be member of an organization (check `organization_members` table)

### Issue: Copy button doesn't work
**Solution:**
- Check browser supports `navigator.clipboard`
- Ensure site is served over HTTPS (or localhost)
- Check browser permissions for clipboard access

### Issue: Keys not appearing in list
**Solution:**
- Check browser console for errors
- Verify Supabase RLS policies allow reading
- Ensure `organization_id` matches user's org

### Issue: Build errors
**Solution:**
- Run `npm install @headlessui/react` (required dependency)
- Check TypeScript errors with `npm run build`

## Files Modified/Created

```
dashboard/
├── app/
│   └── (dashboard)/
│       └── api-keys/
│           ├── page.tsx (NEW)
│           └── actions.ts (NEW)
└── components/
    └── api-keys/
        ├── APIKeyList.tsx (NEW)
        ├── APIKeyGenerateModal.tsx (NEW)
        └── APIKeyDisplay.tsx (NEW)

package.json (MODIFIED - added @headlessui/react)
```

## Next Steps

After successful testing:

1. **Database Migration:** Ensure `api_keys` table exists in production
2. **Environment Variables:** Verify Supabase credentials are set
3. **RLS Policies:** Confirm Row Level Security policies are in place
4. **MCP Server:** Update MCP server to validate API keys
5. **Documentation:** Update user-facing docs with API key setup instructions
6. **Monitoring:** Add logging for API key usage and errors

## Security Notes

- ✅ API keys use cryptographically secure randomness
- ✅ Only SHA-256 hashes stored in database
- ✅ Full keys shown only once
- ✅ Server-side validation on all actions
- ✅ Organization isolation enforced
- ✅ Soft delete maintains audit trail
- ✅ No API keys in client-side state after modal close
