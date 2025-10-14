'use client'

interface UsageData {
  month_year: string
  total_api_requests: number
}

interface UsageChartProps {
  data: UsageData[]
}

export default function UsageChart({ data }: UsageChartProps) {
  // Simple bar chart visualization (could be replaced with Chart.js or Recharts)
  const maxValue = Math.max(...data.map(d => d.total_api_requests), 1)

  return (
    <div className="rounded-lg bg-white shadow p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">
        API Request Volume (Last 30 Days)
      </h2>

      {data.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">No usage data available yet.</p>
          <p className="text-sm text-gray-400 mt-2">
            Make some API requests to see your usage trends.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {data.map((item) => {
            const percentage = (item.total_api_requests / maxValue) * 100
            const monthLabel = new Date(item.month_year + '-01').toLocaleDateString('en-US', {
              month: 'short',
              year: 'numeric',
            })

            return (
              <div key={item.month_year} className="flex items-center gap-4">
                <div className="w-20 text-sm text-gray-600 text-right">
                  {monthLabel}
                </div>
                <div className="flex-1">
                  <div className="relative h-8 bg-gray-100 rounded">
                    <div
                      className="absolute top-0 left-0 h-full bg-blue-500 rounded transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    />
                    <div className="absolute inset-0 flex items-center px-3 text-sm font-medium text-gray-700">
                      {item.total_api_requests.toLocaleString()} requests
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Usage is tracked per calendar month. Chart shows cumulative requests for each month.
        </p>
      </div>
    </div>
  )
}
