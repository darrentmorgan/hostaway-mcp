/**
 * Component Contracts: Data Types & Models
 *
 * TypeScript types for data structures used across dashboard components.
 * These types represent the shape of data fetched from Supabase and passed to components.
 */

// ============================================================================
// Database Entity Types (from Supabase)
// ============================================================================

/**
 * Organization entity
 */
export interface Organization {
  id: string // UUID
  name: string
  created_at: Date
  updated_at: Date
}

/**
 * Organization Member entity
 */
export interface OrganizationMember {
  id: string // UUID
  organization_id: string // UUID
  user_id: string // UUID
  role: 'owner' | 'admin' | 'member'
  created_at: Date
}

/**
 * Hostaway Credentials entity
 */
export interface HostawayCredentials {
  id: string // UUID
  organization_id: string // UUID
  account_id: string
  client_id: string
  client_secret: string // Encrypted
  access_token: string | null
  token_expires_at: Date | null
  created_at: Date
  updated_at: Date
}

/**
 * API Key entity
 */
export interface ApiKey {
  id: string // UUID
  organization_id: string // UUID
  name: string
  key_hash: string
  key_prefix: string // For display (e.g., "sk_...abc123")
  permissions: string[] // JSON array
  expires_at: Date | null
  last_used_at: Date | null
  is_active: boolean
  created_by: string // UUID (user_id)
  created_at: Date
  updated_at: Date
}

/**
 * Subscription entity
 */
export interface Subscription {
  id: string // UUID
  organization_id: string // UUID
  listing_count: number
  base_price: number // USD (e.g., 10.00)
  per_listing_price: number // USD (e.g., 5.00)
  stripe_subscription_id: string | null
  stripe_customer_id: string | null
  status: 'active' | 'canceled' | 'past_due' | 'unpaid'
  current_period_start: Date
  current_period_end: Date
  created_at: Date
  updated_at: Date
}

/**
 * Usage Metrics entity
 */
export interface UsageMetrics {
  id: string // UUID
  organization_id: string // UUID
  month_year: Date // First day of month (e.g., 2025-10-01)
  total_api_requests: number
  listing_count: number
  total_cost: number // USD
  created_at: Date
  updated_at: Date
}

/**
 * Audit Log entity
 */
export interface AuditLog {
  id: string // UUID
  organization_id: string // UUID
  user_id: string | null // UUID
  action: string // e.g., "api_key.created", "credentials.updated"
  resource_type: string // e.g., "api_key", "hostaway_credentials"
  resource_id: string | null // UUID
  metadata: Record<string, any> // JSON
  ip_address: string | null
  user_agent: string | null
  created_at: Date
}

// ============================================================================
// View Model Types (for components)
// ============================================================================

/**
 * Usage page data (aggregated view model)
 */
export interface UsagePageData {
  currentMonthMetrics: {
    totalApiRequests: number
    listingCount: number
    projectedBill: number
    billingPeriod: {
      start: Date
      end: Date
    }
  }
  historicalData: Array<{
    date: string // ISO date string (YYYY-MM-DD)
    totalApiRequests: number
  }>
}

/**
 * Billing page data (aggregated view model)
 */
export interface BillingPageData {
  currentSubscription: {
    status: 'active' | 'canceled' | 'past_due' | 'unpaid'
    listingCount: number
    monthlyPrice: number // USD
    currentPeriodStart: Date
    currentPeriodEnd: Date
  }
  paymentMethod: {
    last4: string
    brand: string
    expiryMonth: number
    expiryYear: number
  } | null
  invoices: Array<{
    id: string
    date: Date
    amount: number // USD
    status: 'paid' | 'pending' | 'failed'
    downloadUrl?: string
  }>
}

/**
 * API Keys page data (aggregated view model)
 */
export interface ApiKeysPageData {
  apiKeys: Array<{
    id: string
    name: string
    keyPrefix: string // Masked (e.g., "sk_...abc123")
    createdAt: Date
    lastUsedAt: Date | null
    status: 'active' | 'revoked'
    createdBy: {
      id: string
      email: string
    }
  }>
}

/**
 * Settings page data (aggregated view model)
 */
export interface SettingsPageData {
  organization: {
    id: string
    name: string
  }
  hostawayCredentials: {
    accountId: string // Masked (e.g., "123***")
    clientId: string // Masked
    isConfigured: boolean
    lastSynced: Date | null
  } | null
  members: Array<{
    id: string
    email: string
    role: 'owner' | 'admin' | 'member'
    joinedAt: Date
  }>
}

// ============================================================================
// Form Data Types
// ============================================================================

/**
 * API Key creation form data
 */
export interface ApiKeyFormData {
  name: string
  permissions: string[]
  expiresAt: Date | null
}

/**
 * Hostaway credentials form data
 */
export interface HostawayCredentialsFormData {
  accountId: string
  clientId: string
  clientSecret: string
}

/**
 * Organization settings form data
 */
export interface OrganizationFormData {
  name: string
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * API error response
 */
export interface ApiError {
  code: string // e.g., "INVALID_CREDENTIALS", "RATE_LIMIT_EXCEEDED"
  message: string
  statusCode: number
  details?: Record<string, any>
}

/**
 * Form validation error
 */
export interface ValidationError {
  field: string
  message: string
}

// ============================================================================
// Loading State Types
// ============================================================================

/**
 * Generic loading state wrapper
 */
export interface LoadingState<T> {
  data: T | null
  isLoading: boolean
  error: ApiError | null
}

/**
 * Mutation state (for form submissions)
 */
export interface MutationState {
  isSubmitting: boolean
  error: ApiError | null
  success: boolean
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  page: number
  pageSize: number
  totalCount: number
  totalPages: number
}

/**
 * Paginated response
 */
export interface PaginatedResponse<T> {
  data: T[]
  meta: PaginationMeta
}

/**
 * Sort configuration
 */
export interface SortConfig<T> {
  key: keyof T
  direction: 'asc' | 'desc'
}

// ============================================================================
// Chart Data Types (for Recharts)
// ============================================================================

/**
 * Usage chart data point
 */
export interface UsageChartDataPoint {
  /**
   * Date string in format "MMM DD" (e.g., "Oct 14")
   * This is the display label on the X-axis
   */
  dateLabel: string

  /**
   * Full ISO date string (YYYY-MM-DD)
   * This is used for sorting and data processing
   */
  date: string

  /**
   * Total API requests for that date
   */
  apiRequests: number
}

/**
 * Billing chart data point (if needed for future charts)
 */
export interface BillingChartDataPoint {
  monthLabel: string // "Oct 2025"
  month: string // "2025-10"
  totalCost: number // USD
  apiRequests: number
}

// ============================================================================
// Context Types (React Context)
// ============================================================================

/**
 * User context (from Supabase Auth)
 */
export interface UserContext {
  id: string // UUID
  email: string
  name: string | null
  avatarUrl: string | null
}

/**
 * Organization context (current active org)
 */
export interface OrganizationContext {
  id: string // UUID
  name: string
  role: 'owner' | 'admin' | 'member'
}

/**
 * Dashboard context (global dashboard state)
 */
export interface DashboardContext {
  user: UserContext
  organization: OrganizationContext
  isLoading: boolean
}

// ============================================================================
// Constants (Enums)
// ============================================================================

/**
 * User roles
 */
export enum UserRole {
  Owner = 'owner',
  Admin = 'admin',
  Member = 'member',
}

/**
 * Subscription status
 */
export enum SubscriptionStatus {
  Active = 'active',
  Canceled = 'canceled',
  PastDue = 'past_due',
  Unpaid = 'unpaid',
}

/**
 * Invoice status
 */
export enum InvoiceStatus {
  Paid = 'paid',
  Pending = 'pending',
  Failed = 'failed',
}

/**
 * Audit log actions
 */
export enum AuditAction {
  ApiKeyCreated = 'api_key.created',
  ApiKeyRevoked = 'api_key.revoked',
  ApiKeyRotated = 'api_key.rotated',
  CredentialsUpdated = 'credentials.updated',
  CredentialsDeleted = 'credentials.deleted',
  OrganizationUpdated = 'organization.updated',
  MemberInvited = 'member.invited',
  MemberRemoved = 'member.removed',
}

// ============================================================================
// Type Guards
// ============================================================================

/**
 * Type guard to check if error is ApiError
 */
export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error &&
    'statusCode' in error
  )
}

/**
 * Type guard to check if value is Date
 */
export function isDate(value: unknown): value is Date {
  return value instanceof Date && !isNaN(value.getTime())
}

// ============================================================================
// Usage Examples
// ============================================================================

/**
 * Example: Fetching usage data
 *
 * ```tsx
 * async function fetchUsageData(orgId: string): Promise<UsagePageData> {
 *   const supabase = createClient()
 *
 *   const { data, error } = await supabase
 *     .from('usage_metrics')
 *     .select('*')
 *     .eq('organization_id', orgId)
 *
 *   if (error) throw new ApiError(...)
 *
 *   return {
 *     currentMonthMetrics: {...},
 *     historicalData: data.map(d => ({
 *       date: d.month_year,
 *       totalApiRequests: d.total_api_requests,
 *     })),
 *   }
 * }
 * ```
 */

/**
 * Example: Using LoadingState
 *
 * ```tsx
 * const [state, setState] = useState<LoadingState<UsagePageData>>({
 *   data: null,
 *   isLoading: true,
 *   error: null,
 * })
 *
 * useEffect(() => {
 *   fetchUsageData(orgId)
 *     .then(data => setState({ data, isLoading: false, error: null }))
 *     .catch(error => setState({ data: null, isLoading: false, error }))
 * }, [orgId])
 * ```
 */
