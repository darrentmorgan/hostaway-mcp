interface MetricsSummaryProps {
  totalRequests: number
  listingCount: number
  projectedBill: number
  uniqueTools: number
}

export default function MetricsSummary({
  totalRequests,
  listingCount,
  projectedBill,
  uniqueTools,
}: MetricsSummaryProps) {
  const metrics = [
    {
      name: 'API Requests (This Month)',
      value: totalRequests.toLocaleString(),
      icon: '📊',
      description: 'Total MCP API calls made',
    },
    {
      name: 'Active Listings',
      value: listingCount.toLocaleString(),
      icon: '🏠',
      description: 'Current Hostaway listings',
    },
    {
      name: 'Projected Monthly Bill',
      value: `$${projectedBill.toFixed(2)}`,
      icon: '💰',
      description: 'Based on current listing count',
    },
    {
      name: 'Unique Tools Used',
      value: uniqueTools.toString(),
      icon: '🔧',
      description: 'Different MCP endpoints accessed',
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => (
        <div
          key={metric.name}
          className="relative overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:px-6 sm:py-6"
        >
          <dt>
            <div className="absolute rounded-md bg-blue-500 p-3">
              <span className="text-2xl">{metric.icon}</span>
            </div>
            <p className="ml-16 truncate text-sm font-medium text-gray-500">
              {metric.name}
            </p>
          </dt>
          <dd className="ml-16 flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900">{metric.value}</p>
          </dd>
          <dd className="ml-16 mt-1">
            <p className="text-xs text-gray-500">{metric.description}</p>
          </dd>
        </div>
      ))}
    </div>
  )
}
