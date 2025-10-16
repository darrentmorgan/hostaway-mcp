import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

interface EmptyStateProps {
  title?: string
  description?: string
  actionLabel?: string
  actionHref?: string
}

export default function EmptyState({
  title = 'No Usage Data Yet',
  description = 'Start using the Hostaway MCP Server to see your usage metrics and analytics here.',
  actionLabel,
  actionHref,
}: EmptyStateProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Usage Overview</CardTitle>
        <CardDescription>Track your API usage and metrics</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-4 text-6xl">📊</div>
          <h3 className="mb-2 text-lg font-semibold">{title}</h3>
          <p className="mb-6 max-w-sm text-sm text-muted-foreground">
            {description}
          </p>
          {actionLabel && actionHref && (
            <Button asChild>
              <Link href={actionHref}>{actionLabel}</Link>
            </Button>
          )}
          {!actionLabel && (
            <div className="space-y-2 text-left">
              <p className="text-sm text-muted-foreground">
                To get started:
              </p>
              <ol className="list-inside list-decimal space-y-1 text-sm text-muted-foreground">
                <li>Configure your API keys</li>
                <li>Set up Hostaway credentials</li>
                <li>Make your first API request</li>
              </ol>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
