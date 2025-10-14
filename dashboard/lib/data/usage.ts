import { createClient } from '@/lib/supabase/server'
import { getCurrentMonth, getMonthsAgo } from '@/lib/utils/date'
import { calculateMonthlyBill } from '@/lib/utils/billing'

export interface UsagePageData {
  currentMonthMetrics: {
    totalApiRequests: number
    listingCount: number
    projectedBill: number
    uniqueTools: number
  } | null
  historicalData: Array<{
    monthYear: string
    totalApiRequests: number
  }>
  error: string | null
}

export async function fetchUsageData(): Promise<UsagePageData> {
  try {
    const supabase = await createClient()

    // Get current user
    const {
      data: { user },
    } = await supabase.auth.getUser()
    if (!user) {
      return {
        currentMonthMetrics: null,
        historicalData: [],
        error: 'Not authenticated',
      }
    }

    // Get organization ID
    const { data: membership, error: membershipError } = await supabase
      .from('organization_members')
      .select('organization_id')
      .eq('user_id', user.id)
      .single()

    if (membershipError || !membership) {
      return {
        currentMonthMetrics: null,
        historicalData: [],
        error: 'Organization not found',
      }
    }

    const organizationId = membership.organization_id

    // Fetch current month metrics
    const currentMonth = getCurrentMonth()
    const { data: currentMetrics, error: metricsError } = await supabase
      .from('usage_metrics')
      .select('*')
      .eq('organization_id', organizationId)
      .eq('month_year', currentMonth)
      .single()

    // PGRST116 means no rows returned - this is OK for new users
    if (metricsError && metricsError.code !== 'PGRST116') {
      throw metricsError
    }

    // Fetch subscription for listing count
    const { data: subscription, error: subscriptionError } = await supabase
      .from('subscriptions')
      .select('current_quantity, status')
      .eq('organization_id', organizationId)
      .eq('status', 'active')
      .single()

    // PGRST116 means no rows returned - this is OK for new users
    if (subscriptionError && subscriptionError.code !== 'PGRST116') {
      throw subscriptionError
    }

    // Fetch last 6 months of historical data
    const sixMonthsAgo = getMonthsAgo(6)
    const { data: historicalMetrics, error: historicalError } = await supabase
      .from('usage_metrics')
      .select('month_year, total_api_requests')
      .eq('organization_id', organizationId)
      .gte('month_year', sixMonthsAgo)
      .order('month_year', { ascending: true })

    if (historicalError) {
      throw historicalError
    }

    // Build current month metrics
    const totalApiRequests = currentMetrics?.total_api_requests || 0
    const listingCount = subscription?.current_quantity || 0
    const uniqueTools = currentMetrics?.unique_tools_used?.length || 0
    const projectedBill = calculateMonthlyBill(listingCount)

    return {
      currentMonthMetrics: {
        totalApiRequests,
        listingCount,
        projectedBill,
        uniqueTools,
      },
      historicalData: (historicalMetrics || []).map((metric) => ({
        monthYear: metric.month_year,
        totalApiRequests: metric.total_api_requests || 0,
      })),
      error: null,
    }
  } catch (error) {
    console.error('Error fetching usage data:', error)
    return {
      currentMonthMetrics: null,
      historicalData: [],
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    }
  }
}
