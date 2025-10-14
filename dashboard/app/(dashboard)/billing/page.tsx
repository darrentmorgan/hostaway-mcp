import { getSubscriptionStatus, createBillingPortalSession, createCheckoutSession, getInvoiceHistory } from './actions'
import { redirect } from 'next/navigation'
import InvoiceHistory from '@/components/billing/InvoiceHistory'

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
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Success/Cancel Messages */}
      {params.success && (
        <div className="mb-6 rounded-md bg-green-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">
                Subscription activated successfully!
              </h3>
            </div>
          </div>
        </div>
      )}

      {params.canceled && (
        <div className="mb-6 rounded-md bg-yellow-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Checkout canceled. No changes were made.
              </h3>
            </div>
          </div>
        </div>
      )}

      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Billing & Subscription</h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage your subscription and billing information.
          </p>
        </div>
      </div>

      {/* Current Subscription Status */}
      {subscriptionData.status === 'active' && subscriptionData.subscription && (
        <div className="mt-8 rounded-lg bg-white shadow px-6 py-5">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Current Subscription</h2>
          <div className="space-y-3">
            <div>
              <span className="text-sm font-medium text-gray-500">Plan: </span>
              <span className="text-sm text-gray-900">{subscriptionData.subscription.plan_name}</span>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-500">Status: </span>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                subscriptionData.subscription.status === 'active'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {subscriptionData.subscription.status}
              </span>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-500">Amount: </span>
              <span className="text-sm text-gray-900">
                ${(subscriptionData.subscription.amount / 100).toFixed(2)} / month
              </span>
            </div>
            {subscriptionData.subscription.cancel_at_period_end && (
              <div className="mt-2 p-3 bg-yellow-50 rounded-md">
                <p className="text-sm text-yellow-800">
                  Your subscription will be canceled at the end of the current billing period (
                  {new Date(subscriptionData.subscription.current_period_end * 1000).toLocaleDateString()}
                  )
                </p>
              </div>
            )}
          </div>
          <div className="mt-6">
            <form action={handleBillingPortal}>
              <button
                type="submit"
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Manage Subscription
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Pricing Plans */}
      {subscriptionData.status !== 'active' && (
        <div className="mt-12">
          <h2 className="text-lg font-medium text-gray-900 mb-6">Choose a Plan</h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {PRICING_PLANS.map((plan) => (
              <div
                key={plan.id}
                className="flex flex-col rounded-lg shadow-lg overflow-hidden border border-gray-200"
              >
                <div className="px-6 py-8 bg-white">
                  <div>
                    <h3 className="text-2xl font-semibold text-gray-900">{plan.name}</h3>
                    <div className="mt-4 flex items-baseline">
                      <span className="text-4xl font-extrabold text-gray-900">${plan.price}</span>
                      <span className="ml-1 text-xl font-semibold text-gray-500">/month</span>
                    </div>
                    <ul className="mt-6 space-y-4">
                      {plan.features.map((feature) => (
                        <li key={feature} className="flex items-start">
                          <svg
                            className="flex-shrink-0 h-5 w-5 text-green-500"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <span className="ml-3 text-sm text-gray-700">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="mt-8">
                    {plan.priceId ? (
                      <form action={handleCheckout.bind(null, plan.priceId)}>
                        <button
                          type="submit"
                          className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                          Subscribe
                        </button>
                      </form>
                    ) : (
                      <button
                        disabled
                        className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white cursor-not-allowed"
                      >
                        Current Plan
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {subscriptionData.status === 'error' && (
        <div className="mt-8 rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Error loading subscription information
              </h3>
              <p className="mt-2 text-sm text-red-700">
                {subscriptionData.error || 'Please try again later'}
              </p>
            </div>
          </div>
        </div>
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
