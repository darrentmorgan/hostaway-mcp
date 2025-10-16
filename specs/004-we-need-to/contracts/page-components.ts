/**
 * Component Contracts: Page-Specific Components
 *
 * TypeScript interfaces for dashboard page components.
 * These are custom components built on top of the base UI components.
 */

import { ReactNode } from 'react'

// ============================================================================
// Usage Page Components
// ============================================================================

/**
 * MetricsSummary Component
 *
 * Displays current month's usage metrics in a card layout with:
 * - API request count
 * - Listing count
 * - Projected billing amount
 * - Billing period dates
 */
export interface MetricsSummaryProps {
  /**
   * Total API requests for current month
   */
  apiRequests: number

  /**
   * Number of active Hostaway listings
   */
  listingCount: number

  /**
   * Projected billing amount (USD)
   */
  projectedBill: number

  /**
   * Current billing period
   */
  billingPeriod: {
    start: Date
    end: Date
  }

  /**
   * Loading state - shows skeleton loaders
   * @default false
   */
  loading?: boolean

  /**
   * Error state
   */
  error?: Error | null
}

/**
 * UsageChart Component
 *
 * Displays 30-day historical API request trend using Recharts LineChart.
 */
export interface UsageChartProps {
  /**
   * Historical usage data (30 days)
   */
  data: Array<{
    /**
     * Date in ISO format (YYYY-MM-DD)
     */
    date: string

    /**
     * Total API requests for that date
     */
    apiRequests: number
  }>

  /**
   * Loading state - shows skeleton chart
   * @default false
   */
  loading?: boolean

  /**
   * Error state
   */
  error?: Error | null
}

/**
 * UsageMetricCard Component
 *
 * Individual metric card (reusable component for MetricsSummary).
 */
export interface UsageMetricCardProps {
  /**
   * Metric label
   */
  label: string

  /**
   * Metric value
   */
  value: string | number

  /**
   * Optional icon
   */
  icon?: ReactNode

  /**
   * Optional subtitle/helper text
   */
  subtitle?: string

  /**
   * Loading state - shows skeleton
   * @default false
   */
  loading?: boolean
}

// ============================================================================
// Billing Page Components
// ============================================================================

/**
 * BillingHistory Component
 *
 * Displays table of past invoices.
 */
export interface BillingHistoryProps {
  /**
   * Array of invoice records
   */
  invoices: Array<{
    id: string
    date: Date
    amount: number
    status: 'paid' | 'pending' | 'failed'
    downloadUrl?: string
  }>

  /**
   * Loading state
   * @default false
   */
  loading?: boolean

  /**
   * Error state
   */
  error?: Error | null
}

/**
 * PaymentMethodCard Component
 *
 * Displays current payment method with update option.
 */
export interface PaymentMethodCardProps {
  /**
   * Card last 4 digits
   */
  last4: string

  /**
   * Card brand (Visa, Mastercard, etc.)
   */
  brand: string

  /**
   * Expiration month (1-12)
   */
  expiryMonth: number

  /**
   * Expiration year (YYYY)
   */
  expiryYear: number

  /**
   * Update handler
   */
  onUpdate: () => void

  /**
   * Loading state
   * @default false
   */
  loading?: boolean
}

// ============================================================================
// API Keys Page Components
// ============================================================================

/**
 * ApiKeyList Component
 *
 * Displays table of API keys with actions (revoke, rotate).
 */
export interface ApiKeyListProps {
  /**
   * Array of API key records
   */
  apiKeys: Array<{
    id: string
    name: string
    key: string // Masked (e.g., "sk_...abc123")
    createdAt: Date
    lastUsed: Date | null
    status: 'active' | 'revoked'
  }>

  /**
   * Revoke key handler
   */
  onRevoke: (id: string) => void

  /**
   * Rotate key handler
   */
  onRotate: (id: string) => void

  /**
   * Loading state
   * @default false
   */
  loading?: boolean

  /**
   * Error state
   */
  error?: Error | null
}

/**
 * CreateApiKeyModal Component
 *
 * Modal dialog for creating a new API key.
 */
export interface CreateApiKeyModalProps {
  /**
   * Whether the modal is open
   */
  open: boolean

  /**
   * Open state change handler
   */
  onOpenChange: (open: boolean) => void

  /**
   * Create key handler
   */
  onCreate: (name: string, permissions: string[]) => Promise<void>

  /**
   * Submitting state
   * @default false
   */
  submitting?: boolean
}

/**
 * ApiKeyCreatedDialog Component
 *
 * Modal showing newly created API key (one-time display).
 */
export interface ApiKeyCreatedDialogProps {
  /**
   * Whether the dialog is open
   */
  open: boolean

  /**
   * Open state change handler
   */
  onOpenChange: (open: boolean) => void

  /**
   * Newly created API key (full, unmasked)
   */
  apiKey: string

  /**
   * Key name
   */
  keyName: string
}

// ============================================================================
// Settings Page Components
// ============================================================================

/**
 * HostawayCredentialsForm Component
 *
 * Form for updating Hostaway API credentials.
 */
export interface HostawayCredentialsFormProps {
  /**
   * Current account ID (masked)
   */
  currentAccountId?: string

  /**
   * Submit handler
   */
  onSubmit: (credentials: {
    accountId: string
    clientId: string
    clientSecret: string
  }) => Promise<void>

  /**
   * Submitting state
   * @default false
   */
  submitting?: boolean

  /**
   * Error state
   */
  error?: Error | null
}

/**
 * OrganizationSettingsForm Component
 *
 * Form for updating organization details.
 */
export interface OrganizationSettingsFormProps {
  /**
   * Current organization name
   */
  currentName: string

  /**
   * Submit handler
   */
  onSubmit: (name: string) => Promise<void>

  /**
   * Submitting state
   * @default false
   */
  submitting?: boolean

  /**
   * Error state
   */
  error?: Error | null
}

// ============================================================================
// Layout Components
// ============================================================================

/**
 * DashboardNav Component
 *
 * Main navigation sidebar/header.
 */
export interface DashboardNavProps {
  /**
   * Current active page
   */
  activePage: 'home' | 'usage' | 'billing' | 'api-keys' | 'settings'

  /**
   * User information
   */
  user: {
    name: string
    email: string
    avatarUrl?: string
  }

  /**
   * Organization information
   */
  organization: {
    name: string
  }

  /**
   * Logout handler
   */
  onLogout: () => void
}

/**
 * PageHeader Component
 *
 * Page title and breadcrumbs.
 */
export interface PageHeaderProps {
  /**
   * Page title
   */
  title: string

  /**
   * Optional description
   */
  description?: string

  /**
   * Optional breadcrumb items
   */
  breadcrumbs?: Array<{
    label: string
    href?: string
  }>

  /**
   * Optional action button
   */
  action?: ReactNode
}

/**
 * EmptyState Component
 *
 * Generic empty state with icon, message, and optional action.
 */
export interface EmptyStateProps {
  /**
   * Icon to display
   */
  icon?: ReactNode

  /**
   * Primary message
   */
  title: string

  /**
   * Secondary message
   */
  description?: string

  /**
   * Optional action button
   */
  action?: ReactNode
}

/**
 * ErrorState Component
 *
 * Generic error state with retry option.
 */
export interface ErrorStateProps {
  /**
   * Error message
   */
  message: string

  /**
   * Optional error code
   */
  code?: string

  /**
   * Retry handler
   */
  onRetry?: () => void

  /**
   * Retrying state
   * @default false
   */
  retrying?: boolean
}

/**
 * LoadingState Component
 *
 * Generic loading state with skeleton loaders.
 */
export interface LoadingStateProps {
  /**
   * Loading message
   */
  message?: string

  /**
   * Number of skeleton rows
   * @default 3
   */
  skeletonRows?: number
}

// ============================================================================
// Usage Examples
// ============================================================================

/**
 * Example: MetricsSummary usage
 *
 * ```tsx
 * <MetricsSummary
 *   apiRequests={1234}
 *   listingCount={56}
 *   projectedBill={12.50}
 *   billingPeriod={{
 *     start: new Date('2025-10-01'),
 *     end: new Date('2025-10-31'),
 *   }}
 *   loading={false}
 *   error={null}
 * />
 * ```
 */

/**
 * Example: UsageChart usage
 *
 * ```tsx
 * <UsageChart
 *   data={[
 *     { date: '2025-09-15', apiRequests: 120 },
 *     { date: '2025-09-16', apiRequests: 145 },
 *     // ... 28 more days
 *   ]}
 *   loading={false}
 *   error={null}
 * />
 * ```
 */

/**
 * Example: ApiKeyList usage
 *
 * ```tsx
 * <ApiKeyList
 *   apiKeys={[
 *     {
 *       id: '123',
 *       name: 'Production Key',
 *       key: 'sk_...abc123',
 *       createdAt: new Date('2025-09-01'),
 *       lastUsed: new Date('2025-10-14'),
 *       status: 'active',
 *     },
 *   ]}
 *   onRevoke={(id) => console.log('Revoke', id)}
 *   onRotate={(id) => console.log('Rotate', id)}
 *   loading={false}
 *   error={null}
 * />
 * ```
 */

/**
 * Example: DashboardNav usage
 *
 * ```tsx
 * <DashboardNav
 *   activePage="usage"
 *   user={{
 *     name: 'John Doe',
 *     email: 'john@example.com',
 *     avatarUrl: 'https://...',
 *   }}
 *   organization={{
 *     name: 'Acme Corp',
 *   }}
 *   onLogout={() => signOut()}
 * />
 * ```
 */
