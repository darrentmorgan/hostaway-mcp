import {
  getSubscriptionStatus,
  createBillingPortalSession,
  createCheckoutSession,
  getInvoiceHistory,
} from './actions'
import { redirect } from 'next/navigation'
import InvoiceHistory from '@/components/billing/InvoiceHistory'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'

// Define pricing plans (these should match your Stripe products)
const PRICING_PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    priceId: null, // No Stripe price ID for free tier
    features: [
      '100 API requests per month',
      '1 Hostaway account',
      'Basic support',
      '7-day data retention',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 29,
    priceId: process.env.STRIPE_PRO_PRICE_ID || 'price_pro', // Replace with actual Stripe price ID
    features: [
      '10,000 API requests per month',
      '5 Hostaway accounts',
      'Priority support',
      '90-day data retention',
      'Advanced analytics',
    ],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 99,
    priceId: process.env.STRIPE_ENTERPRISE_PRICE_ID || 'price_enterprise', // Replace with actual Stripe price ID
    features: [
      'Unlimited API requests',
      'Unlimited Hostaway accounts',
      '24/7 dedicated support',
      'Unlimited data retention',
      'Advanced analytics',
      'Custom integrations',
    ],
  },
]

async function handleBillingPortal() {
  'use server'
  const result = await createBillingPortalSession()
  if (result.url) {
    redirect(result.url)
  }
}

async function handleCheckout(priceId: string) {
  'use server'
  const result = await createCheckoutSession(priceId)
  if (result.url) {
    redirect(result.url)
  }
}

export default async function BillingPage({
  searchParams,
}: {
  searchParams: Promise<{ success?: string; canceled?: string }>
}) {
  const subscriptionData = await getSubscriptionStatus()
  const invoiceHistory = await getInvoiceHistory()
  const params = await searchParams

  return (
    <div className="space-y-8">
      {/* Success/Cancel Messages */}
      {params.success && (
        <Alert>
          <AlertTitle>Success!</AlertTitle>
          <AlertDescription>
            Subscription activated successfully!
          </AlertDescription>
        </Alert>
      )}

      {params.canceled && (
        <Alert variant="destructive">
          <AlertTitle>Checkout Canceled</AlertTitle>
          <AlertDescription>
            Checkout canceled. No changes were made.
          </AlertDescription>
        </Alert>
      )}

      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Billing & Subscription
        </h1>
        <p className="mt-2 text-muted-foreground">
          Manage your subscription and billing information.
        </p>
      </div>

      {/* Current Subscription Status */}
      {subscriptionData.status === 'active' &&
        subscriptionData.subscription && (
          <Card>
            <CardHeader>
              <CardTitle>Current Subscription</CardTitle>
              <CardDescription>
                Your active subscription details
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Plan
                  </p>
                  <p className="text-lg font-semibold">
                    {subscriptionData.subscription.plan_name}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Status
                  </p>
                  <Badge
                    variant={
                      subscriptionData.subscription.status === 'active'
                        ? 'default'
                        : 'secondary'
                    }
                  >
                    {subscriptionData.subscription.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Amount
                  </p>
                  <p className="text-lg font-semibold">
                    ${(subscriptionData.subscription.amount / 100).toFixed(2)}{' '}
                    / month
                  </p>
                </div>
              </div>

              {subscriptionData.subscription.cancel_at_period_end && (
                <Alert variant="destructive">
                  <AlertDescription>
                    Your subscription will be canceled at the end of the
                    current billing period (
                    {new Date(
                      subscriptionData.subscription.current_period_end * 1000
                    ).toLocaleDateString()}
                    )
                  </AlertDescription>
                </Alert>
              )}

              <form action={handleBillingPortal} className="pt-4">
                <Button type="submit" variant="outline">
                  Manage Subscription
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

      {/* Pricing Plans */}
      {subscriptionData.status !== 'active' && (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold">Choose a Plan</h2>
            <p className="mt-2 text-muted-foreground">
              Select the plan that best fits your needs
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {PRICING_PLANS.map((plan) => (
              <Card key={plan.id} className="flex flex-col">
                <CardHeader>
                  <CardTitle className="text-2xl">{plan.name}</CardTitle>
                  <div className="mt-4 flex items-baseline">
                    <span className="text-4xl font-bold">${plan.price}</span>
                    <span className="ml-2 text-xl text-muted-foreground">
                      /month
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col">
                  <ul className="space-y-3 flex-1">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-3">
                        <svg
                          className="h-5 w-5 shrink-0 text-primary"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-8">
                    {plan.priceId ? (
                      <form action={handleCheckout.bind(null, plan.priceId)}>
                        <Button type="submit" className="w-full">
                          Subscribe
                        </Button>
                      </form>
                    ) : (
                      <Button disabled variant="outline" className="w-full">
                        Current Plan
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {subscriptionData.status === 'error' && (
        <Alert variant="destructive">
          <AlertTitle>Error Loading Subscription</AlertTitle>
          <AlertDescription>
            {subscriptionData.error || 'Please try again later'}
          </AlertDescription>
        </Alert>
      )}

      {/* Invoice History (T052) */}
      {subscriptionData.status === 'active' && invoiceHistory.invoices.length > 0 && (
        <div className="mt-12">
          <InvoiceHistory invoices={invoiceHistory.invoices} />
        </div>
      )}
    </div>
  )
}
