# Component Contracts

**Date**: 2025-10-14
**Feature**: Production-Ready Dashboard with Design System
**Phase**: 1 (Design & Contracts)

## Overview

This directory contains TypeScript interface definitions (contracts) for all dashboard components. These contracts serve as design-time documentation and will guide implementation.

---

## Files

### `ui-components.ts`

**Base UI component interfaces** from shadcn/ui:

- Button (6 variants: default, primary, secondary, ghost, link, destructive)
- Card (with Header, Title, Description, Content, Footer)
- Input (text, email, password, number, tel, url)
- Table (with sorting, pagination, custom rendering)
- Dialog/Modal (with Header, Title, Description, Footer)
- Skeleton (loading placeholders)
- Alert (info, warning, error, success)
- Badge (status indicators)
- Select (dropdown)
- Tooltip (contextual help)
- Form (with validation)

**Total**: 10+ base components

---

### `page-components.ts`

**Page-specific component interfaces** for dashboard pages:

**Usage Page**:
- `MetricsSummary` - Display API requests, listing count, projected bill
- `UsageChart` - 30-day historical API request trend (Recharts)
- `UsageMetricCard` - Individual metric card

**Billing Page**:
- `BillingHistory` - Table of past invoices
- `PaymentMethodCard` - Current payment method with update option

**API Keys Page**:
- `ApiKeyList` - Table of API keys with actions
- `CreateApiKeyModal` - Modal for creating new API key
- `ApiKeyCreatedDialog` - One-time display of new key

**Settings Page**:
- `HostawayCredentialsForm` - Update Hostaway API credentials
- `OrganizationSettingsForm` - Update organization details

**Layout Components**:
- `DashboardNav` - Main navigation sidebar/header
- `PageHeader` - Page title and breadcrumbs
- `EmptyState` - Generic empty state
- `ErrorState` - Generic error state
- `LoadingState` - Generic loading state

**Total**: 15+ page-specific components

---

### `data-types.ts`

**Data structure types** for database entities and view models:

**Database Entities** (from Supabase):
- `Organization`
- `OrganizationMember`
- `HostawayCredentials`
- `ApiKey`
- `Subscription`
- `UsageMetrics`
- `AuditLog`

**View Models** (aggregated data for pages):
- `UsagePageData`
- `BillingPageData`
- `ApiKeysPageData`
- `SettingsPageData`

**Form Data Types**:
- `ApiKeyFormData`
- `HostawayCredentialsFormData`
- `OrganizationFormData`

**Error Types**:
- `ApiError`
- `ValidationError`

**Loading State Types**:
- `LoadingState<T>`
- `MutationState`

**Utility Types**:
- `PaginationMeta`
- `PaginatedResponse<T>`
- `SortConfig<T>`

**Chart Data Types**:
- `UsageChartDataPoint`
- `BillingChartDataPoint`

**Context Types**:
- `UserContext`
- `OrganizationContext`
- `DashboardContext`

**Enums**:
- `UserRole`
- `SubscriptionStatus`
- `InvoiceStatus`
- `AuditAction`

**Total**: 30+ type definitions

---

## Usage in Implementation

### 1. Import Base Components

```typescript
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
```

### 2. Import Page Components

```typescript
import { MetricsSummary } from '@/components/usage/metrics-summary'
import { UsageChart } from '@/components/usage/usage-chart'
```

### 3. Import Data Types

```typescript
import type { UsagePageData, LoadingState } from '@/contracts/data-types'
```

### 4. Use Interfaces in Component Props

```typescript
// Example: Implementing MetricsSummary component
import type { MetricsSummaryProps } from '@/contracts/page-components'

export function MetricsSummary({
  apiRequests,
  listingCount,
  projectedBill,
  billingPeriod,
  loading = false,
  error = null,
}: MetricsSummaryProps) {
  // Component implementation
}
```

---

## Contract Principles

### 1. Type Safety

All component props are strongly typed. No `any` types allowed.

### 2. Loading States

All data-fetching components accept `loading?: boolean` prop to show skeleton loaders.

### 3. Error States

All data-fetching components accept `error?: Error | null` prop to show error messages.

### 4. Optional Props

Props with defaults (e.g., `variant`, `size`) are marked as optional with `?`.

### 5. Children

Components that accept children use `children: ReactNode` type.

### 6. Event Handlers

Event handlers use clear naming: `onClick`, `onChange`, `onSubmit`, `onRetry`.

### 7. Accessibility

All interactive components support keyboard navigation and ARIA attributes (handled by Radix UI).

---

## Relationship to Implementation

**These contracts are design-time documentation**, not runtime code. During implementation:

1. **shadcn/ui components** (Button, Card, etc.) will be installed via CLI and may have additional props not listed here.
2. **Page-specific components** (MetricsSummary, UsageChart, etc.) will be implemented using these contracts as the source of truth.
3. **Data types** will be used throughout the codebase for type-safe data fetching and state management.

---

## Examples

### Example 1: Button Usage

```tsx
import { Button } from '@/components/ui/button'

<Button variant="primary" size="lg" onClick={handleSubmit}>
  Submit
</Button>

<Button variant="destructive" disabled>
  Delete
</Button>
```

### Example 2: Card Usage

```tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

<Card>
  <CardHeader>
    <CardTitle>API Usage</CardTitle>
  </CardHeader>
  <CardContent>
    <p>1,234 requests this month</p>
  </CardContent>
</Card>
```

### Example 3: MetricsSummary Usage

```tsx
import { MetricsSummary } from '@/components/usage/metrics-summary'

<MetricsSummary
  apiRequests={1234}
  listingCount={56}
  projectedBill={12.50}
  billingPeriod={{
    start: new Date('2025-10-01'),
    end: new Date('2025-10-31'),
  }}
  loading={false}
  error={null}
/>
```

### Example 4: Data Fetching with LoadingState

```tsx
import type { UsagePageData, LoadingState } from '@/contracts/data-types'

const [state, setState] = useState<LoadingState<UsagePageData>>({
  data: null,
  isLoading: true,
  error: null,
})

useEffect(() => {
  fetchUsageData(orgId)
    .then(data => setState({ data, isLoading: false, error: null }))
    .catch(error => setState({ data: null, isLoading: false, error }))
}, [orgId])

if (state.isLoading) return <LoadingState />
if (state.error) return <ErrorState error={state.error} onRetry={refetch} />
if (!state.data) return <EmptyState title="No data available" />

return <MetricsSummary {...state.data.currentMonthMetrics} />
```

---

## Validation

To verify contracts are being followed during implementation:

1. **TypeScript Compiler**: All implementations must pass `tsc --noEmit` with no errors
2. **ESLint**: Use `@typescript-eslint/consistent-type-definitions` rule
3. **Code Review**: Verify all component props match contract interfaces

---

## Next Steps

After contracts are defined:

1. ✅ Contracts created and documented
2. → Run `/speckit.tasks` to generate implementation tasks
3. → Implement shadcn/ui base components
4. → Implement page-specific components using contracts
5. → Run TypeScript compiler to verify type safety

---

**Status**: ✅ **CONTRACTS COMPLETE**
**Date**: 2025-10-14
**Next Phase**: Task Generation (`/speckit.tasks`)
