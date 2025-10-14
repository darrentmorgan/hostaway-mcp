import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import MetricsSummary from '@/components/usage/MetricsSummary'
import UsageChart from '@/components/usage/UsageChart'

export default async function UsagePage() {
  const supabase = await createClient()

  // Check if user is authenticated
  const { data: { user }, error: userError } = await supabase.auth.getUser()

  if (userError || !user) {
    redirect('/login')
  }

  // Get user's organization membership
  const { data: membership, error: membershipError } = await supabase
    .from('organization_members')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  if (membershipError || !membership) {
    redirect('/login')
  }

  // Get current month metrics
  const currentMonth = new Date().toISOString().substring(0, 7) // YYYY-MM format
  const { data: metrics } = await supabase
    .from('usage_metrics')
    .select('*')
    .eq('organization_id', membership.organization_id)
    .eq('month_year', currentMonth)
    .single()

  // Get subscription for listing count
  const { data: subscription } = await supabase
    .from('subscriptions')
    .select('current_quantity, status')
    .eq('organization_id', membership.organization_id)
    .eq('status', 'active')
    .single()

  // Get last 30 days of metrics for chart
  const thirtyDaysAgo = new Date()
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
  const startMonth = thirtyDaysAgo.toISOString().substring(0, 7)

  const { data: historicalMetrics } = await supabase
    .from('usage_metrics')
    .select('month_year, total_api_requests')
    .eq('organization_id', membership.organization_id)
    .gte('month_year', startMonth)
    .order('month_year', { ascending: true })

  const totalRequests = metrics?.total_api_requests || 0
  const listingCount = subscription?.current_quantity || 0
  const uniqueTools = metrics?.unique_tools_used?.length || 0

  // Calculate projected bill (example: $5/listing/month)
  const pricePerListing = 5
  const projectedBill = listingCount * pricePerListing

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Page Header */}
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-3xl font-bold text-gray-900">Usage & Metrics</h1>
          <p className="mt-2 text-sm text-gray-700">
            Monitor your API usage, listing count, and billing projections.
          </p>
        </div>
      </div>

      {/* Metrics Summary Cards */}
      <div className="mt-8">
        <MetricsSummary
          totalRequests={totalRequests}
          listingCount={listingCount}
          projectedBill={projectedBill}
          uniqueTools={uniqueTools}
        />
      </div>

      {/* Usage Chart */}
      <div className="mt-8">
        <UsageChart data={historicalMetrics || []} />
      </div>

      {/* Sync Notice */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">About Usage Metrics</h3>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>API requests are tracked in real-time as you use MCP tools.</li>
          <li>Listing count syncs daily from your Hostaway account.</li>
          <li>Projected bill is based on current listing count at ${pricePerListing}/listing/month.</li>
          <li>Unique tools shows how many different MCP endpoints you've used this month.</li>
        </ul>
      </div>
    </div>
  )
}
