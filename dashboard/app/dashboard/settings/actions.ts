'use server'
import { createClient } from '@/lib/supabase/server'
import {
  logError,
  ErrorMessages,
  createErrorResponse,
  createSuccessResponse,
} from '@/lib/utils/errors'

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

  if (!user) {
    return createErrorResponse(
      ErrorMessages.NOT_AUTHENTICATED,
      logError('User not authenticated', new Error('No user session'))
    )
  }

  const { data: membership, error: memberError } = await supabase
    .from('organization_members')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  if (memberError) {
    const correlationId = logError('Failed to fetch organization membership', memberError, {
      userId: user.id,
    })
    return createErrorResponse(ErrorMessages.ORGANIZATION_LOAD_FAILED, correlationId)
  }

  if (!membership) {
    return createErrorResponse(
      ErrorMessages.ORGANIZATION_NOT_FOUND,
      logError('No organization found', new Error('Organization not found'), { userId: user.id })
    )
  }

  const { error } = await supabase
    .from('hostaway_credentials')
    .delete()
    .eq('organization_id', membership.organization_id)

  if (error) {
    const correlationId = logError('Failed to delete Hostaway credentials', error, {
      organizationId: membership.organization_id,
    })
    return createErrorResponse(ErrorMessages.HOSTAWAY_CONNECTION_FAILED, correlationId)
  }

  return createSuccessResponse({})
}

export async function refreshHostawayConnection() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return createErrorResponse(
      ErrorMessages.NOT_AUTHENTICATED,
      logError('User not authenticated', new Error('No user session'))
    )
  }

  const { data: membership, error: memberError } = await supabase
    .from('organization_members')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  if (memberError) {
    const correlationId = logError('Failed to fetch organization membership', memberError, {
      userId: user.id,
    })
    return createErrorResponse(ErrorMessages.ORGANIZATION_LOAD_FAILED, correlationId)
  }

  if (!membership) {
    return createErrorResponse(
      ErrorMessages.ORGANIZATION_NOT_FOUND,
      logError('No organization found', new Error('Organization not found'), { userId: user.id })
    )
  }

  // Get existing credentials
  const { data: credentials, error: credError } = await supabase
    .from('hostaway_credentials')
    .select('account_id, encrypted_secret_key')
    .eq('organization_id', membership.organization_id)
    .single()

  if (credError && credError.code !== 'PGRST116') {
    const correlationId = logError('Failed to fetch Hostaway credentials', credError, {
      organizationId: membership.organization_id,
    })
    return createErrorResponse(ErrorMessages.DATABASE_ERROR, correlationId)
  }

  if (!credentials) {
    return createErrorResponse(
      ErrorMessages.HOSTAWAY_NO_CREDENTIALS,
      logError('No credentials found', new Error('Credentials not found'), {
        organizationId: membership.organization_id,
      })
    )
  }

  // Re-validate and refresh using existing credentials
  return connectHostaway(credentials.account_id, credentials.encrypted_secret_key)
}

export async function connectHostaway(accountId: string, secretKey: string) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return createErrorResponse(
      ErrorMessages.NOT_AUTHENTICATED,
      logError('User not authenticated', new Error('No user session'))
    )
  }

  const { data: membership, error: memberError } = await supabase
    .from('organization_members')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  if (memberError) {
    const correlationId = logError('Failed to fetch organization membership', memberError, {
      userId: user.id,
    })
    return createErrorResponse(ErrorMessages.ORGANIZATION_LOAD_FAILED, correlationId)
  }

  if (!membership) {
    return createErrorResponse(
      ErrorMessages.ORGANIZATION_NOT_FOUND,
      logError('No organization found', new Error('Organization not found'), { userId: user.id })
    )
  }

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

    if (credError) {
      const correlationId = logError('Failed to save Hostaway credentials', credError, {
        organizationId: membership.organization_id,
      })
      return createErrorResponse(ErrorMessages.CREDENTIALS_SAVE_FAILED, correlationId)
    }

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

    // Log metrics failure but don't fail the connection - warn user instead
    let warning: string | undefined
    if (metricsError) {
      const correlationId = logError('Failed to store usage metrics', metricsError, {
        organizationId: membership.organization_id,
        monthYear,
        listingCount,
      })
      warning = `Connection successful, but usage metrics could not be saved. Reference: ${correlationId}`
    }

    return createSuccessResponse({ listingCount }, warning)
  } catch (error) {
    const correlationId = logError('Hostaway connection failed', error, {
      organizationId: membership.organization_id,
    })

    // Provide specific error messages based on error type
    if (error instanceof Error) {
      if (error.message.includes('authentication failed')) {
        return createErrorResponse(ErrorMessages.HOSTAWAY_AUTH_FAILED, correlationId)
      }
      if (error.message.includes('Failed to fetch')) {
        return createErrorResponse(ErrorMessages.HOSTAWAY_CONNECTION_FAILED, correlationId)
      }
    }

    return createErrorResponse(ErrorMessages.HOSTAWAY_CONNECTION_FAILED, correlationId)
  }
}
