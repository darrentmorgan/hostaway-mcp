import { fetchUsageData } from '@/lib/data/usage'
import MetricsSummary from '@/components/usage/MetricsSummary'
import UsageChart from '@/components/usage/UsageChart'
import EmptyState from '@/components/usage/EmptyState'
import ErrorState from '@/components/usage/ErrorState'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

export default async function UsagePage() {
  // Fetch all usage data
  const { currentMonthMetrics, historicalData, error } = await fetchUsageData()

  // Handle error state
  if (error) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Usage & Metrics</h1>
          <p className="mt-2 text-muted-foreground">
            Monitor your API usage, listing count, and billing projections
          </p>
        </div>
        <ErrorState error={error} />
      </div>
    )
  }

  // Handle empty state (no metrics data)
  if (!currentMonthMetrics) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Usage & Metrics</h1>
          <p className="mt-2 text-muted-foreground">
            Monitor your API usage, listing count, and billing projections
          </p>
        </div>
        <EmptyState
          title="No Usage Data Yet"
          description="Start using the Hostaway MCP Server to see your usage metrics and analytics here."
          actionLabel="Configure API Keys"
          actionHref="/api-keys"
        />
      </div>
    )
  }

  // Extract metrics for display
  const { totalApiRequests, listingCount, projectedBill, uniqueTools } =
    currentMonthMetrics

  // Check if user has no listings configured
  const hasNoListings = listingCount === 0

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Usage & Metrics</h1>
        <p className="mt-2 text-muted-foreground">
          Monitor your API usage, listing count, and billing projections
        </p>
      </div>

      {/* Warning for no listings */}
      {hasNoListings && (
        <Alert>
          <AlertTitle>No Listings Found</AlertTitle>
          <AlertDescription>
            Connect your Hostaway account in Settings to sync your property
            listings and enable full usage tracking.
          </AlertDescription>
        </Alert>
      )}

      {/* Metrics Summary Cards */}
      <MetricsSummary
        totalRequests={totalApiRequests}
        listingCount={listingCount}
        projectedBill={projectedBill}
        uniqueTools={uniqueTools}
      />

      {/* Usage Chart */}
      <UsageChart data={historicalData} />

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>About Usage Metrics</CardTitle>
          <CardDescription>
            How your usage data is tracked and calculated
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="mt-0.5">•</span>
              <span>
                API requests are tracked in real-time as you use MCP tools
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5">•</span>
              <span>Listing count syncs daily from your Hostaway account</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5">•</span>
              <span>
                Projected bill is calculated based on your current listing count
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5">•</span>
              <span>
                Unique tools shows how many different MCP endpoints you&apos;ve
                used this month
              </span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
