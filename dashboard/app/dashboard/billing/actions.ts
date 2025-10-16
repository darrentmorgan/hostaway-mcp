'use server'

import { createClient } from '@/lib/supabase/server'
import { createServiceRoleClient } from '@/lib/supabase/service-role'
import Stripe from 'stripe'
import { redirect } from 'next/navigation'

// Lazy Stripe client initialization to prevent app crash if key is missing
let stripeClient: Stripe | null = null

function getStripeClient(): Stripe {
  if (!stripeClient) {
    const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY
    if (!STRIPE_SECRET_KEY) {
      throw new Error('Missing required environment variable: STRIPE_SECRET_KEY')
    }
    stripeClient = new Stripe(STRIPE_SECRET_KEY, {
      apiVersion: '2025-09-30.clover',
    })
  }
  return stripeClient
}

/**
 * Create a billing portal session for the current user's organization
 */
export async function createBillingPortalSession() {
  try {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
      return { error: 'Not authenticated' }
    }

    // Get user's organization
    const { data: membership, error: memberError } = await supabase
      .from('organization_members')
      .select('organization_id')
      .eq('user_id', user.id)
      .single()

    if (memberError) {
      console.error('Failed to fetch organization membership:', memberError)
      return { error: 'Failed to load organization. Please try again.' }
    }

    if (!membership) {
      return { error: 'No organization found' }
    }

    // Get organization with Stripe customer ID
    const { data: organization, error: orgError } = await supabase
      .from('organizations')
      .select('stripe_customer_id')
      .eq('id', membership.organization_id)
      .single()

    if (orgError) {
      console.error('Failed to fetch organization:', orgError)
      return { error: 'Failed to load organization details. Please try again.' }
    }

    if (!organization?.stripe_customer_id) {
      return { error: 'No Stripe customer found' }
    }

    // Create billing portal session
    const stripe = getStripeClient()
    const session = await stripe.billingPortal.sessions.create({
      customer: organization.stripe_customer_id,
      return_url: `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001'}/billing`,
    })

    return { url: session.url }
  } catch (error) {
    console.error('Error creating billing portal session:', error)
    if (error instanceof Error && error.message.includes('STRIPE_SECRET_KEY')) {
      return { error: 'Billing is not configured. Please contact support.' }
    }
    return { error: 'Failed to create billing portal session' }
  }
}

/**
 * Create a subscription checkout session
 */
export async function createCheckoutSession(priceId: string) {
  try {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
      return { error: 'Not authenticated' }
    }

    // Get user's organization
    const { data: membership, error: memberError } = await supabase
      .from('organization_members')
      .select('organization_id')
      .eq('user_id', user.id)
      .single()

    if (memberError) {
      console.error('Failed to fetch organization membership:', memberError)
      return { error: 'Failed to load organization. Please try again.' }
    }

    if (!membership) {
      return { error: 'No organization found' }
    }

    // Get organization with Stripe customer ID
    const { data: organization, error: orgError } = await supabase
      .from('organizations')
      .select('stripe_customer_id, name')
      .eq('id', membership.organization_id)
      .single()

    if (orgError) {
      console.error('Failed to fetch organization:', orgError)
      return { error: 'Failed to load organization details. Please try again.' }
    }

    if (!organization?.stripe_customer_id) {
      return { error: 'No Stripe customer found' }
    }

    // Create checkout session
    const stripe = getStripeClient()
    const session = await stripe.checkout.sessions.create({
      customer: organization.stripe_customer_id,
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      success_url: `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001'}/billing?success=true`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001'}/billing?canceled=true`,
      metadata: {
        organization_id: membership.organization_id,
      },
    })

    return { url: session.url }
  } catch (error) {
    console.error('Error creating checkout session:', error)
    if (error instanceof Error && error.message.includes('STRIPE_SECRET_KEY')) {
      return { error: 'Billing is not configured. Please contact support.' }
    }
    return { error: 'Failed to create checkout session' }
  }
}

/**
 * Get current subscription status for user's organization
 */
export async function getSubscriptionStatus() {
  try {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
      return { status: 'unauthenticated' as const }
    }

    // Get user's organization
    const { data: membership, error: memberError } = await supabase
      .from('organization_members')
      .select('organization_id')
      .eq('user_id', user.id)
      .single()

    if (memberError) {
      console.error('Failed to fetch organization membership:', memberError)
      return { status: 'error' as const, error: 'Failed to load organization' }
    }

    if (!membership) {
      return { status: 'no_organization' as const }
    }

    // Get organization with Stripe customer ID
    const { data: organization, error: orgError } = await supabase
      .from('organizations')
      .select('stripe_customer_id, name')
      .eq('id', membership.organization_id)
      .single()

    if (orgError) {
      console.error('Failed to fetch organization:', orgError)
      return { status: 'error' as const, error: 'Failed to load organization details' }
    }

    if (!organization?.stripe_customer_id) {
      return { status: 'no_customer' as const, organization }
    }

    // Get subscriptions from Stripe
    const stripe = getStripeClient()
    const subscriptions = await stripe.subscriptions.list({
      customer: organization.stripe_customer_id,
      status: 'all',
      limit: 1,
      expand: ['data.items.data.price'],
    })

    if (subscriptions.data.length === 0) {
      return {
        status: 'no_subscription' as const,
        organization,
        customerId: organization.stripe_customer_id,
      }
    }

    const subscription = subscriptions.data[0]
    // Type assertion needed due to Stripe API version changes
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const sub = subscription as any

    return {
      status: 'active' as const,
      organization,
      subscription: {
        id: sub.id,
        status: sub.status,
        current_period_end: sub.current_period_end,
        cancel_at_period_end: sub.cancel_at_period_end,
        plan_name: sub.items.data[0]?.price.nickname || 'Subscription',
        amount: sub.items.data[0]?.price.unit_amount || 0,
        currency: sub.items.data[0]?.price.currency || 'usd',
      },
    }
  } catch (error) {
    console.error('Error getting subscription status:', error)
    return { status: 'error' as const, error: 'Failed to get subscription status' }
  }
}

/**
 * Get invoice history for user's organization (T049)
 */
export async function getInvoiceHistory() {
  try {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
      return { error: 'Not authenticated', invoices: [] }
    }

    // Get user's organization
    const { data: membership, error: memberError } = await supabase
      .from('organization_members')
      .select('organization_id')
      .eq('user_id', user.id)
      .single()

    if (memberError) {
      console.error('Failed to fetch organization membership:', memberError)
      return { error: 'Failed to load organization', invoices: [] }
    }

    if (!membership) {
      return { error: 'No organization found', invoices: [] }
    }

    // Get organization with Stripe customer ID
    const { data: organization, error: orgError } = await supabase
      .from('organizations')
      .select('stripe_customer_id')
      .eq('id', membership.organization_id)
      .single()

    if (orgError) {
      console.error('Failed to fetch organization:', orgError)
      return { error: 'Failed to load organization details', invoices: [] }
    }

    if (!organization?.stripe_customer_id) {
      return { error: 'No Stripe customer found', invoices: [] }
    }

    // Fetch invoices from Stripe
    const stripe = getStripeClient()
    const invoices = await stripe.invoices.list({
      customer: organization.stripe_customer_id,
      limit: 12, // Last 12 invoices (approximately 1 year)
    })

    const formattedInvoices = invoices.data.map(invoice => ({
      id: invoice.id,
      date: invoice.created,
      amount: invoice.amount_paid,
      currency: invoice.currency,
      status: invoice.status,
      invoice_pdf: invoice.invoice_pdf || null,
      hosted_invoice_url: invoice.hosted_invoice_url || null,
      period_start: invoice.period_start,
      period_end: invoice.period_end,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      listing_count: (invoice.lines.data[0] as any)?.quantity || 0,
    }))

    return { invoices: formattedInvoices }
  } catch (error) {
    console.error('Error fetching invoice history:', error)
    return { error: 'Failed to fetch invoice history', invoices: [] }
  }
}
