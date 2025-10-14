import { createClient } from '@/lib/supabase/server'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default async function DashboardPage() {
  const supabase = await createClient()

  // Get user info
  const {
    data: { user },
  } = await supabase.auth.getUser()

  // Get organization info
  const { data: membership } = await supabase
    .from('organization_members')
    .select('organization_id, organizations(name)')
    .eq('user_id', user?.id || '')
    .single()

  const organizationName = membership?.organizations
    ? Array.isArray(membership.organizations)
      ? membership.organizations[0]?.name
      : (membership.organizations as { name: string })?.name
    : null

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-4xl font-bold tracking-tight">
          Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}!
        </h1>
        <p className="mt-2 text-lg text-muted-foreground">
          {organizationName
            ? `Managing ${organizationName}`
            : 'Manage your Hostaway MCP integration'}
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              API Requests
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">-</div>
            <p className="mt-1 text-xs text-muted-foreground">
              This month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Listings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">-</div>
            <p className="mt-1 text-xs text-muted-foreground">
              Synced from Hostaway
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              API Keys
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">-</div>
            <p className="mt-1 text-xs text-muted-foreground">Active keys</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Projected Bill
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">$0.00</div>
            <p className="mt-1 text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>
      </div>

      {/* Getting Started */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
            <CardDescription>
              Complete these steps to start using the MCP integration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
                1
              </div>
              <div>
                <p className="font-medium">Configure Hostaway Credentials</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Add your Hostaway Account ID and Secret Key in Settings
                </p>
                <Link href="/settings">
                  <Button variant="link" className="mt-2 h-auto p-0">
                    Go to Settings →
                  </Button>
                </Link>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold">
                2
              </div>
              <div>
                <p className="font-medium">Generate an API Key</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Create an API key to authenticate your MCP client
                </p>
                <Link href="/api-keys">
                  <Button variant="link" className="mt-2 h-auto p-0">
                    Manage API Keys →
                  </Button>
                </Link>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold">
                3
              </div>
              <div>
                <p className="font-medium">Monitor Usage</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  View API request metrics and billing projections
                </p>
                <Link href="/usage">
                  <Button variant="link" className="mt-2 h-auto p-0">
                    View Usage →
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Links</CardTitle>
            <CardDescription>
              Commonly used features and resources
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link
              href="/api-keys"
              className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-accent"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">🔑</span>
                <div>
                  <p className="font-medium">API Keys</p>
                  <p className="text-sm text-muted-foreground">
                    Manage authentication
                  </p>
                </div>
              </div>
              <span className="text-muted-foreground">→</span>
            </Link>

            <Link
              href="/billing"
              className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-accent"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">💳</span>
                <div>
                  <p className="font-medium">Billing</p>
                  <p className="text-sm text-muted-foreground">
                    View invoices & payment
                  </p>
                </div>
              </div>
              <span className="text-muted-foreground">→</span>
            </Link>

            <Link
              href="/settings"
              className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-accent"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">⚙️</span>
                <div>
                  <p className="font-medium">Settings</p>
                  <p className="text-sm text-muted-foreground">
                    Configure credentials
                  </p>
                </div>
              </div>
              <span className="text-muted-foreground">→</span>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Support Alert */}
      <Alert>
        <AlertTitle>Need Help?</AlertTitle>
        <AlertDescription>
          Check out our documentation or contact support if you have any
          questions about setting up your MCP integration.
        </AlertDescription>
      </Alert>
    </div>
  )
}
