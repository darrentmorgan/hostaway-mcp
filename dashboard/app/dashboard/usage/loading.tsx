import MetricsSummary from '@/components/usage/MetricsSummary'
import UsageChart from '@/components/usage/UsageChart'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

export default function Loading() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Usage & Metrics</h1>
        <p className="mt-2 text-muted-foreground">
          Monitor your API usage, listing count, and billing projections
        </p>
      </div>

      {/* Metrics Summary Cards - Loading State */}
      <MetricsSummary
        totalRequests={0}
        listingCount={0}
        projectedBill={0}
        uniqueTools={0}
        loading={true}
      />

      {/* Usage Chart - Loading State */}
      <UsageChart data={[]} loading={true} />

      {/* Info Card - Loading State */}
      <Card>
        <CardHeader>
          <CardTitle>About Usage Metrics</CardTitle>
          <CardDescription>
            How your usage data is tracked and calculated
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-full" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
