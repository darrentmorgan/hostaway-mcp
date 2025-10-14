# Data Model: Component Models & Design Tokens

**Date**: 2025-10-14
**Feature**: Production-Ready Dashboard with Design System
**Phase**: 1 (Design & Contracts)

## Overview

**Note**: This is a **UI-focused feature** with no database changes. This document describes **component models** (props, state, design tokens), not database schemas.

---

## Design Tokens

Design tokens are centralized style values that ensure visual consistency across all components.

### Color Tokens

```typescript
// CSS Variables (defined in app/globals.css)
:root {
  --background: 0 0% 100%;           // #FFFFFF
  --foreground: 222.2 84% 4.9%;      // #020817

  --card: 0 0% 100%;                 // #FFFFFF
  --card-foreground: 222.2 84% 4.9%; // #020817

  --popover: 0 0% 100%;              // #FFFFFF
  --popover-foreground: 222.2 84% 4.9%; // #020817

  --primary: 221.2 83.2% 53.3%;      // #3B82F6 (Blue)
  --primary-foreground: 210 40% 98%; // #F8FAFC

  --secondary: 210 40% 96.1%;        // #F1F5F9
  --secondary-foreground: 222.2 47.4% 11.2%; // #1E293B

  --muted: 210 40% 96.1%;            // #F1F5F9
  --muted-foreground: 215.4 16.3% 46.9%; // #64748B

  --accent: 210 40% 96.1%;           // #F1F5F9
  --accent-foreground: 222.2 47.4% 11.2%; // #1E293B

  --destructive: 0 84.2% 60.2%;      // #EF4444 (Red)
  --destructive-foreground: 210 40% 98%; // #F8FAFC

  --border: 214.3 31.8% 91.4%;       // #E2E8F0
  --input: 214.3 31.8% 91.4%;        // #E2E8F0
  --ring: 221.2 83.2% 53.3%;         // #3B82F6

  --radius: 0.5rem;                  // 8px
}

.dark {
  --background: 222.2 84% 4.9%;      // #020817
  --foreground: 210 40% 98%;         // #F8FAFC
  // ... (dark mode values - out of scope for Phase 1)
}
```

### Typography Tokens

```typescript
// Font Scale (Tailwind classes)
{
  xs: "text-xs",      // 12px
  sm: "text-sm",      // 14px
  base: "text-base",  // 16px
  lg: "text-lg",      // 18px
  xl: "text-xl",      // 20px
  "2xl": "text-2xl",  // 24px
  "3xl": "text-3xl",  // 30px
  "4xl": "text-4xl",  // 36px
}

// Font Weights
{
  normal: "font-normal",    // 400
  medium: "font-medium",    // 500
  semibold: "font-semibold", // 600
  bold: "font-bold",        // 700
}

// Line Heights
{
  tight: "leading-tight",   // 1.25
  normal: "leading-normal", // 1.5
  relaxed: "leading-relaxed", // 1.625
}
```

### Spacing Tokens

```typescript
// Spacing Scale (Tailwind classes)
{
  0: "0px",
  1: "0.25rem",  // 4px
  2: "0.5rem",   // 8px
  3: "0.75rem",  // 12px
  4: "1rem",     // 16px
  5: "1.25rem",  // 20px
  6: "1.5rem",   // 24px
  8: "2rem",     // 32px
  10: "2.5rem",  // 40px
  12: "3rem",    // 48px
  16: "4rem",    // 64px
}

// Container Padding
{
  "container-padding": "2rem", // 32px
  "card-padding": "1.5rem",    // 24px
  "section-spacing": "3rem",   // 48px
}
```

### Border Radius Tokens

```typescript
// Border Radius (CSS variables)
{
  "radius-sm": "calc(var(--radius) - 4px)", // 4px
  "radius-md": "calc(var(--radius) - 2px)", // 6px
  "radius-lg": "var(--radius)",             // 8px
  "radius-xl": "calc(var(--radius) + 4px)", // 12px
  "radius-full": "9999px",                  // Fully rounded
}
```

### Shadow Tokens

```typescript
// Shadows (Tailwind classes)
{
  sm: "shadow-sm",   // 0 1px 2px 0 rgb(0 0 0 / 0.05)
  md: "shadow-md",   // 0 4px 6px -1px rgb(0 0 0 / 0.1)
  lg: "shadow-lg",   // 0 10px 15px -3px rgb(0 0 0 / 0.1)
  xl: "shadow-xl",   // 0 20px 25px -5px rgb(0 0 0 / 0.1)
}
```

---

## Component Models

### 1. Button Component

**Purpose**: Primary interactive element for user actions.

**Props Interface**:
```typescript
export interface ButtonProps {
  variant?: 'default' | 'primary' | 'secondary' | 'ghost' | 'link' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
  type?: 'button' | 'submit' | 'reset'
  children: React.ReactNode
  className?: string
}
```

**States**:
- Default: Base styling
- Hover: Background darkens, cursor pointer
- Active: Background pressed effect
- Focus: Ring outline (keyboard navigation)
- Disabled: Opacity 50%, cursor not-allowed
- Loading: Spinner icon, disabled state

**Visual Variants**:
- `default`: White background, border, black text
- `primary`: Primary color background, white text
- `secondary`: Secondary color background, dark text
- `ghost`: Transparent background, hover shows background
- `link`: Text-only, underline on hover
- `destructive`: Red background, white text (danger actions)

---

### 2. Card Component

**Purpose**: Container for grouping related content with consistent spacing and borders.

**Props Interface**:
```typescript
export interface CardProps {
  children: React.ReactNode
  className?: string
  padding?: 'sm' | 'md' | 'lg'
}

export interface CardHeaderProps {
  children: React.ReactNode
  className?: string
}

export interface CardTitleProps {
  children: React.ReactNode
  className?: string
}

export interface CardDescriptionProps {
  children: React.ReactNode
  className?: string
}

export interface CardContentProps {
  children: React.ReactNode
  className?: string
}

export interface CardFooterProps {
  children: React.ReactNode
  className?: string
}
```

**Composition**:
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Main content */}
  </CardContent>
  <CardFooter>
    {/* Actions */}
  </CardFooter>
</Card>
```

---

### 3. Input Component

**Purpose**: Text input field for forms.

**Props Interface**:
```typescript
export interface InputProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url'
  placeholder?: string
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
  disabled?: boolean
  error?: boolean
  errorMessage?: string
  label?: string
  required?: boolean
  className?: string
}
```

**States**:
- Default: Border color muted
- Focus: Border color ring (primary)
- Error: Border color destructive, error message below
- Disabled: Opacity 50%, cursor not-allowed

---

### 4. Table Component

**Purpose**: Display tabular data with sorting and pagination.

**Props Interface**:
```typescript
export interface TableColumn<T> {
  key: keyof T
  header: string
  render?: (value: T[keyof T], row: T) => React.ReactNode
  sortable?: boolean
  width?: string
}

export interface TableProps<T> {
  data: T[]
  columns: TableColumn<T>[]
  loading?: boolean
  emptyMessage?: string
  onRowClick?: (row: T) => void
  sortBy?: keyof T
  sortDirection?: 'asc' | 'desc'
  onSort?: (key: keyof T, direction: 'asc' | 'desc') => void
}
```

**States**:
- Loading: Skeleton rows with pulse animation
- Empty: Empty state message with icon
- Error: Error message with retry button
- Success: Rendered data rows

---

### 5. Modal/Dialog Component

**Purpose**: Modal overlay for confirmations, forms, and detailed views.

**Props Interface**:
```typescript
export interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}

export interface DialogContentProps {
  children: React.ReactNode
  className?: string
}

export interface DialogHeaderProps {
  children: React.ReactNode
  className?: string
}

export interface DialogTitleProps {
  children: React.ReactNode
  className?: string
}

export interface DialogDescriptionProps {
  children: React.ReactNode
  className?: string
}

export interface DialogFooterProps {
  children: React.ReactNode
  className?: string
}
```

**Accessibility**:
- Focus trap: Tab cycles within modal
- Escape key: Closes modal
- Click outside: Closes modal (optional)
- ARIA attributes: `role="dialog"`, `aria-labelledby`, `aria-describedby`

---

### 6. Skeleton Component

**Purpose**: Loading placeholder for content.

**Props Interface**:
```typescript
export interface SkeletonProps {
  className?: string
  width?: string
  height?: string
  variant?: 'text' | 'circular' | 'rectangular'
}
```

**Animation**:
- Pulse animation: `animate-pulse` (Tailwind)
- Background gradient: Shimmer effect from left to right

---

### 7. Alert Component

**Purpose**: Display important messages (info, warning, error, success).

**Props Interface**:
```typescript
export interface AlertProps {
  variant?: 'default' | 'info' | 'warning' | 'error' | 'success'
  title?: string
  description?: string
  dismissible?: boolean
  onDismiss?: () => void
  children?: React.ReactNode
  className?: string
}
```

**Visual Variants**:
- `default`: Gray background, gray text
- `info`: Blue background, blue text
- `warning`: Yellow background, yellow text
- `error`: Red background, red text
- `success`: Green background, green text

---

### 8. Badge Component

**Purpose**: Small status indicator or label.

**Props Interface**:
```typescript
export interface BadgeProps {
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error'
  children: React.ReactNode
  className?: string
}
```

---

### 9. Select Component

**Purpose**: Dropdown selection field.

**Props Interface**:
```typescript
export interface SelectProps {
  options: Array<{ value: string; label: string }>
  value?: string
  onChange?: (value: string) => void
  placeholder?: string
  disabled?: boolean
  error?: boolean
  label?: string
  required?: boolean
  className?: string
}
```

---

### 10. Tooltip Component

**Purpose**: Contextual help text on hover.

**Props Interface**:
```typescript
export interface TooltipProps {
  content: string | React.ReactNode
  children: React.ReactNode
  side?: 'top' | 'right' | 'bottom' | 'left'
  delay?: number
}
```

---

## Page-Specific Component Models

### Usage Page Components

#### MetricsSummary Component

**Purpose**: Display current month's usage metrics in card format.

**Props Interface**:
```typescript
export interface MetricsSummaryProps {
  apiRequests: number
  listingCount: number
  projectedBill: number
  billingPeriod: { start: Date; end: Date }
  loading?: boolean
  error?: Error | null
}
```

**State**:
```typescript
interface MetricsSummaryState {
  metricsData: {
    apiRequests: number
    listingCount: number
    projectedBill: number
    billingPeriod: { start: Date; end: Date }
  } | null
  isLoading: boolean
  error: Error | null
}
```

---

#### UsageChart Component

**Purpose**: Display 30-day API request trend chart.

**Props Interface**:
```typescript
export interface UsageChartProps {
  data: Array<{
    date: string // ISO date string
    apiRequests: number
  }>
  loading?: boolean
  error?: Error | null
}
```

**State**:
```typescript
interface UsageChartState {
  chartData: Array<{ date: string; apiRequests: number }> | null
  isLoading: boolean
  error: Error | null
}
```

---

## Data Fetching Models

### Server Component Data Fetching

```typescript
// Usage page server component (app/(dashboard)/usage/page.tsx)
interface UsagePageData {
  currentMonthMetrics: {
    totalApiRequests: number
    listingCount: number
    projectedBill: number
    billingPeriod: { start: Date; end: Date }
  }
  historicalData: Array<{
    date: string
    totalApiRequests: number
  }>
}

async function fetchUsageData(organizationId: string): Promise<UsagePageData> {
  // Supabase query for usage_metrics and subscriptions tables
  const supabase = createClient()

  const [metricsResponse, historicalResponse] = await Promise.all([
    supabase
      .from('usage_metrics')
      .select('*')
      .eq('organization_id', organizationId)
      .gte('month_year', getCurrentMonthStart())
      .single(),

    supabase
      .from('usage_metrics')
      .select('month_year, total_api_requests')
      .eq('organization_id', organizationId)
      .gte('month_year', get30DaysAgo())
      .order('month_year', { ascending: true }),
  ])

  return {
    currentMonthMetrics: {
      totalApiRequests: metricsResponse.data?.total_api_requests ?? 0,
      listingCount: metricsResponse.data?.listing_count ?? 0,
      projectedBill: calculateProjectedBill(metricsResponse.data),
      billingPeriod: getCurrentBillingPeriod(),
    },
    historicalData: historicalResponse.data ?? [],
  }
}
```

---

## State Management Models

### Client Component State (React State)

```typescript
// Example: Form state for API key creation
interface ApiKeyFormState {
  name: string
  permissions: string[]
  expiresAt: Date | null
  isSubmitting: boolean
  error: string | null
}

// Example: Modal state
interface ModalState {
  isOpen: boolean
  data: any | null
}
```

---

## Validation Models

### Form Validation

```typescript
// Zod schema for form validation (example)
import { z } from 'zod'

export const apiKeyFormSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters'),
  permissions: z.array(z.string()).min(1, 'Select at least one permission'),
  expiresAt: z.date().nullable(),
})

export type ApiKeyFormData = z.infer<typeof apiKeyFormSchema>
```

---

## Accessibility Models

### Focus Management

```typescript
// Focus trap for modals (handled by Radix UI)
interface FocusTrapProps {
  enabled: boolean
  onEscape?: () => void
  onClickOutside?: () => void
}
```

### Keyboard Navigation

```typescript
// Keyboard event handlers
interface KeyboardNavigationProps {
  onArrowUp?: () => void
  onArrowDown?: () => void
  onEnter?: () => void
  onEscape?: () => void
  onTab?: () => void
}
```

---

## Error Models

### Error States

```typescript
// Generic error state for components
interface ErrorState {
  hasError: boolean
  errorMessage: string | null
  errorCode?: string
  retryAction?: () => void
}

// Specific error types
type LoadingError = {
  type: 'loading'
  message: string
}

type ValidationError = {
  type: 'validation'
  field: string
  message: string
}

type NetworkError = {
  type: 'network'
  message: string
  statusCode?: number
}
```

---

## Performance Models

### Loading States

```typescript
// Skeleton loader configuration
interface SkeletonConfig {
  rows: number
  columns?: number
  height?: string
  variant: 'text' | 'rectangular' | 'circular'
}

// Loading state for data fetching
interface LoadingState<T> {
  data: T | null
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}
```

---

## Summary

This data model document defines:

1. **Design Tokens**: Color, typography, spacing, border radius, shadow values
2. **Base Component Models**: 10 reusable UI components (Button, Card, Input, Table, Modal, Skeleton, Alert, Badge, Select, Tooltip)
3. **Page-Specific Components**: Usage page components (MetricsSummary, UsageChart)
4. **Data Fetching Models**: Server component data fetching patterns
5. **State Management Models**: Client component state patterns
6. **Validation Models**: Form validation with Zod
7. **Accessibility Models**: Focus trap, keyboard navigation
8. **Error Models**: Error states and error types
9. **Performance Models**: Loading states and skeleton loaders

All component models use TypeScript interfaces for type safety and include clear prop definitions, state shapes, and usage patterns.
