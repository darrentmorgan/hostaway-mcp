'use client'

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { formatMonthYear } from '@/lib/utils/date'

interface UsageChartProps {
  data: Array<{
    monthYear: string
    totalApiRequests: number
  }>
  loading?: boolean
}

export default function UsageChart({ data, loading = false }: UsageChartProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Usage Trend</CardTitle>
          <CardDescription>API requests over time</CardDescription>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    )
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Usage Trend</CardTitle>
          <CardDescription>API requests over time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex h-[300px] items-center justify-center text-center">
            <div>
              <p className="text-muted-foreground">
                No usage data available yet.
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                Make some API requests to see your usage trends.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Format data for Recharts
  const chartData = data.map((item) => ({
    month: formatMonthYear(item.monthYear),
    requests: item.totalApiRequests,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Usage Trend</CardTitle>
        <CardDescription>
          API request volume over the last {data.length} months
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 12 }}
              tickMargin={10}
              className="text-muted-foreground"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickMargin={10}
              className="text-muted-foreground"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            <Line
              type="monotone"
              dataKey="requests"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={{ fill: 'hsl(var(--primary))', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
        <p className="mt-4 text-xs text-muted-foreground">
          Usage is tracked per calendar month. Chart shows cumulative requests
          for each month.
        </p>
      </CardContent>
    </Card>
  )
}
