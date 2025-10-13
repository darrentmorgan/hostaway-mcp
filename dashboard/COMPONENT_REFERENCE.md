# Component Reference Guide

Quick reference for the authentication and settings components.

---

## Pages

### Signup Page
**Path**: `/signup`
**File**: `/app/(auth)/signup/page.tsx`
**Type**: Client Component

**Usage**:
```tsx
// Navigate to this page
router.push('/signup')
```

**Props**: None (standalone page)

**Features**:
- Email/password signup
- Password confirmation
- Auto-redirect to /login on success

---

### Login Page
**Path**: `/login`
**File**: `/app/(auth)/login/page.tsx`
**Type**: Client Component

**Usage**:
```tsx
// Navigate to this page
router.push('/login')
```

**Props**: None (standalone page)

**Features**:
- Email/password login
- Auto-redirect to /dashboard on success
- Remember me checkbox
- Forgot password link

---

### Settings Page
**Path**: `/settings`
**File**: `/app/(dashboard)/settings/page.tsx`
**Type**: Server Component

**Protected**: Yes (requires authentication)

**Features**:
- User account info display
- Hostaway credentials management
- Role-based access control
- Server Actions for credential updates

---

## Components

### HostawayCredentials

**File**: `/components/settings/HostawayCredentials.tsx`
**Type**: Client Component

**Props**:
```typescript
interface HostawayCredentialsProps {
  isConnected: boolean              // Current connection status
  accountId?: string                // Current account ID (if connected)
  lastValidated?: string | null     // Last validation timestamp
  onConnect: (accountId: string, secretKey: string) => Promise<void>
  onDisconnect?: () => Promise<void> // Optional disconnect handler
}
```

**Usage Example**:
```tsx
import HostawayCredentials from '@/components/settings/HostawayCredentials'

// In a Server Component
async function handleConnect(accountId: string, secretKey: string) {
  'use server'
  // Your server action logic here
}

// In your page
<HostawayCredentials
  isConnected={hasValidCredentials}
  accountId="12345"
  lastValidated="2024-10-13T12:00:00Z"
  onConnect={handleConnect}
/>
```

**States**:
- **Not Connected**: Shows connection form
- **Connected**: Shows account details and update button
- **Edit Mode**: Shows form to update credentials

---

## Authentication Flow

### User Registration
```
1. User visits /signup
2. Enters email, password, confirm password
3. Supabase creates auth user
4. Email confirmation sent (optional)
5. Redirect to /login
6. [Future] T020 creates organization after email confirmation
```

### User Login
```
1. User visits /login
2. Enters email and password
3. Supabase validates credentials
4. Session created
5. Redirect to /dashboard
```

### Settings Access
```
1. User navigates to /settings (while logged in)
2. Server checks authentication
3. Server fetches organization membership
4. Page displays user info and credential status
5. User can connect/update Hostaway credentials
```

---

## Server Actions

### connectHostaway

**Location**: `/app/(dashboard)/settings/page.tsx`

**Signature**:
```typescript
async function connectHostaway(accountId: string, secretKey: string): Promise<void>
```

**Flow**:
1. Verify user authentication
2. Get user's organization
3. Check user has owner/admin role
4. Encrypt secret key using Supabase RPC
5. Insert or update credentials in database

**Throws**:
- "Unauthorized" - User not authenticated
- "No organization found for user" - No membership record
- "Insufficient permissions" - User is not owner/admin
- "Failed to encrypt secret key" - Encryption error
- "Failed to save credentials" - Database error

---

## Supabase Integration

### Client Usage (Browser)
```typescript
import { createClient } from '@/lib/supabase/client'

const supabase = createClient()

// Signup
const { data, error } = await supabase.auth.signUp({
  email,
  password,
})

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email,
  password,
})
```

### Server Usage (Server Components / Actions)
```typescript
import { createClient } from '@/lib/supabase/server'

const supabase = await createClient()

// Get current user
const { data: { user }, error } = await supabase.auth.getUser()

// Query database
const { data, error } = await supabase
  .from('organization_members')
  .select('*')
  .eq('user_id', user.id)
```

---

## Styling Guide

All components use **Tailwind CSS v4** with consistent design tokens:

### Color Palette
- Primary: `blue-600` (buttons, links)
- Success: `green-100/800` (badges, success messages)
- Error: `red-50/800` (error messages)
- Warning: `yellow-50/800` (info messages)
- Neutral: `gray-50/900` (backgrounds, text)

### Component Patterns

**Form Input**:
```tsx
<input
  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
/>
```

**Primary Button**:
```tsx
<button
  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
>
```

**Card Container**:
```tsx
<div className="bg-white shadow rounded-lg p-6">
```

**Error Message**:
```tsx
<div className="rounded-md bg-red-50 p-4">
  <h3 className="text-sm font-medium text-red-800">Error message</h3>
</div>
```

**Success Message**:
```tsx
<div className="rounded-md bg-green-50 p-4">
  <h3 className="text-sm font-medium text-green-800">Success message</h3>
</div>
```

---

## Route Groups Explained

### (auth)
- **Purpose**: Auth-related pages (login, signup)
- **Layout**: No special layout (uses root layout)
- **Protection**: Public access
- **Location**: `/app/(auth)/`

### (dashboard)
- **Purpose**: Protected app pages
- **Layout**: Should have dashboard layout (to be created)
- **Protection**: Requires authentication
- **Location**: `/app/(dashboard)/`

---

## Error Handling Patterns

### Client-Side Validation
```typescript
const validateForm = () => {
  if (!email || !password) {
    setError('All fields are required')
    return false
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    setError('Please enter a valid email address')
    return false
  }

  return true
}
```

### Server-Side Error Handling
```typescript
try {
  // Database operation
  const { data, error } = await supabase.from('table').insert(data)

  if (error) {
    throw new Error('Database operation failed')
  }
} catch (err) {
  console.error('Server error:', err)
  throw new Error('User-friendly error message')
}
```

### Display Errors
```tsx
{error && (
  <div className="rounded-md bg-red-50 p-4">
    <div className="flex">
      <div className="ml-3">
        <h3 className="text-sm font-medium text-red-800">{error}</h3>
      </div>
    </div>
  </div>
)}
```

---

## TypeScript Types

### Database Types
```typescript
import type { Tables } from '@/lib/types/database'

// Table row types
type Organization = Tables<'organizations'>
type Member = Tables<'organization_members'>
type Credentials = Tables<'hostaway_credentials'>

// Enum types
type Role = 'owner' | 'admin' | 'member'
```

### Component Props
```typescript
// Always define prop interfaces
interface MyComponentProps {
  required: string
  optional?: number
  callback: (data: string) => Promise<void>
}

export default function MyComponent({
  required,
  optional,
  callback
}: MyComponentProps) {
  // Component logic
}
```

---

## Common Patterns

### Protected Page Pattern
```typescript
export default async function ProtectedPage() {
  const supabase = await createClient()

  // Check authentication
  const { data: { user }, error } = await supabase.auth.getUser()

  if (error || !user) {
    redirect('/login')
  }

  // Page content
  return <div>Protected content</div>
}
```

### Server Action Pattern
```typescript
async function myServerAction(data: string) {
  'use server'

  const supabase = await createClient()

  // Verify auth
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('Unauthorized')

  // Business logic
  // ...
}
```

### Form Submission Pattern
```typescript
const [loading, setLoading] = useState(false)
const [error, setError] = useState<string | null>(null)

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  setError(null)

  if (!validateForm()) return

  setLoading(true)
  try {
    await onSubmit(formData)
  } catch (err) {
    setError(err instanceof Error ? err.message : 'An error occurred')
  } finally {
    setLoading(false)
  }
}
```

---

## Testing Hooks

### Where to Add Tests

**Unit Tests**: `/dashboard/__tests__/components/`
```typescript
// HostawayCredentials.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import HostawayCredentials from '@/components/settings/HostawayCredentials'

test('shows connection form when not connected', () => {
  render(<HostawayCredentials isConnected={false} onConnect={jest.fn()} />)
  expect(screen.getByText('Hostaway Account ID')).toBeInTheDocument()
})
```

**Integration Tests**: `/dashboard/__tests__/integration/`
```typescript
// settings.test.tsx
test('authenticated user can access settings', async () => {
  // Mock Supabase auth
  // Visit /settings
  // Verify page loads
})
```

---

## Quick Commands

```bash
# Development
cd dashboard
npm run dev

# Build
npm run build

# Type check
npx tsc --noEmit

# Lint
npm run lint

# Start production server
npm start
```

---

## Helpful Links

- [Next.js App Router Docs](https://nextjs.org/docs/app)
- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
