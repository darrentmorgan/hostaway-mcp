import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatCurrency } from '@/lib/utils/billing'

interface MetricsSummaryProps {
  totalRequests: number
  listingCount: number
  projectedBill: number
  uniqueTools: number
  loading?: boolean
}

export default function MetricsSummary({
  totalRequests,
  listingCount,
  projectedBill,
  uniqueTools,
  loading = false,
}: MetricsSummaryProps) {
  const metrics = [
    {
      name: 'API Requests',
      value: totalRequests.toLocaleString(),
      icon: '📊',
      description: 'This month',
    },
    {
      name: 'Active Listings',
      value: listingCount.toLocaleString(),
      icon: '🏠',
      description: 'From Hostaway',
    },
    {
      name: 'Projected Bill',
      value: formatCurrency(projectedBill),
      icon: '💰',
      description: 'This month',
    },
    {
      name: 'Unique Tools',
      value: uniqueTools.toString(),
      icon: '🔧',
      description: 'MCP endpoints used',
    },
  ]

  if (loading) {
    return (
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-3">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="mt-2 h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => (
        <Card key={metric.name}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {metric.name}
            </CardTitle>
            <span className="text-2xl">{metric.icon}</span>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{metric.value}</div>
            <p className="mt-1 text-xs text-muted-foreground">
              {metric.description}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
