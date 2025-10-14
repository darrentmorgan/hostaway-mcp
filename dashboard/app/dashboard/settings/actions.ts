'use server'
import { createClient } from '@/lib/supabase/server'

/**
 * Get OAuth access token from Hostaway
 */
async function getHostawayToken(accountId: string, secretKey: string): Promise<string> {
  const response = await fetch('https://api.hostaway.com/v1/accessTokens', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Cache-control': 'no-cache',
    },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: accountId,
      client_secret: secretKey,
      scope: 'general',
    }),
  })

  if (!response.ok) {
    throw new Error(`Hostaway authentication failed: ${response.statusText}`)
  }

  const data = await response.json()
  return data.access_token
}

/**
 * Get listing count from Hostaway API
 */
async function getListingCount(accessToken: string): Promise<number> {
  const response = await fetch('https://api.hostaway.com/v1/listings?limit=1&offset=0', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Cache-control': 'no-cache',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch listings: ${response.statusText}`)
  }

  const data = await response.json()
  return data.count || data.result?.length || 0
}

export async function disconnectHostaway() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { success: false, error: 'Not authenticated' }

  const { data: membership } = await supabase
    .from('organization_members')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  if (!membership) return { success: false, error: 'No organization found' }

  const { error } = await supabase
    .from('hostaway_credentials')
    .delete()
    .eq('organization_id', membership.organization_id)

  if (error) return { success: false, error: error.message }
  return { success: true }
}

export async function refreshHostawayConnection() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { success: false, error: 'Not authenticated' }

  const { data: membership } = await supabase
    .from('organization_members')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  if (!membership) return { success: false, error: 'No organization found' }

  // Get existing credentials
  const { data: credentials } = await supabase
    .from('hostaway_credentials')
    .select('account_id, encrypted_secret_key')
    .eq('organization_id', membership.organization_id)
    .single()

  if (!credentials) {
    return { success: false, error: 'No existing credentials found' }
  }

  // Re-validate and refresh using existing credentials
  return connectHostaway(credentials.account_id, credentials.encrypted_secret_key)
}

export async function connectHostaway(accountId: string, secretKey: string) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { success: false, error: 'Not authenticated' }

  const { data: membership } = await supabase
    .from('organization_members')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  if (!membership) return { success: false, error: 'No organization found' }

  try {
    // Validate credentials with Hostaway API
    const accessToken = await getHostawayToken(accountId, secretKey)

    // Get listing count
    const listingCount = await getListingCount(accessToken)

    // Store credentials
    const { error: credError } = await supabase
      .from('hostaway_credentials')
      .upsert({
        organization_id: membership.organization_id,
        account_id: accountId,
        encrypted_secret_key: secretKey, // TODO: Encrypt with Vault
        credentials_valid: true,
        last_validated_at: new Date().toISOString(),
      }, {
        onConflict: 'organization_id'
      })

    if (credError) return { success: false, error: credError.message }

    // Store listing count in usage_metrics for current month
    const now = new Date()
    const monthYear = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

    const { error: metricsError } = await supabase
      .from('usage_metrics')
      .upsert({
        organization_id: membership.organization_id,
        month_year: monthYear,
        listing_count_snapshot: listingCount,
        total_api_requests: 0,
        unique_tools_used: [],
      }, {
        onConflict: 'organization_id,month_year'
      })

    if (metricsError) {
      console.error('Failed to store listing count:', metricsError)
      // Don't fail the whole operation if metrics storage fails
    }

    return { success: true, listingCount }
  } catch (error) {
    console.error('Hostaway connection error:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to connect to Hostaway'
    }
  }
}
