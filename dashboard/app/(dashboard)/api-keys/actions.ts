'use server'

import { createClient } from '@/lib/supabase/server'
import { revalidatePath } from 'next/cache'
import * as crypto from 'crypto'

type ActionResult<T> =
  | { success: true } & T
  | { success: false; error: string }

/**
 * Generates a secure random API key with format: mcp_<32 random chars>
 */
function generateSecureApiKey(): string {
  const randomBytes = crypto.randomBytes(24) // 24 bytes = 32 base64 chars
  const randomString = randomBytes.toString('base64')
    .replace(/[+/=]/g, '') // Remove special chars
    .substring(0, 32)

  return `mcp_${randomString}`
}

/**
 * Hashes an API key using SHA-256
 */
function hashApiKey(apiKey: string): string {
  return crypto.createHash('sha256').update(apiKey).digest('hex')
}

/**
 * Server Action: Generate a new API key for the user's organization
 * Returns the full API key (shown only once) or an error
 */
export async function generateApiKey(): Promise<ActionResult<{ apiKey: string; keyId: number }>> {
  try {
    const supabase = await createClient()

    // 1. Get authenticated user
    const { data: { user }, error: userError } = await supabase.auth.getUser()

    if (userError || !user) {
      return { success: false, error: 'Not authenticated' }
    }

    // 2. Get user's organization
    const { data: membership, error: membershipError } = await supabase
      .from('organization_members')
      .select('organization_id')
      .eq('user_id', user.id)
      .single()

    if (membershipError || !membership) {
      return { success: false, error: 'No organization found for user' }
    }

    const organizationId = membership.organization_id

    // 3. Check if organization has < 5 active API keys
    const { count, error: countError } = await supabase
      .from('api_keys')
      .select('*', { count: 'exact', head: true })
      .eq('organization_id', organizationId)
      .eq('is_active', true)

    if (countError) {
      return { success: false, error: 'Failed to check existing API keys' }
    }

    if (count !== null && count >= 5) {
      return {
        success: false,
        error: 'Maximum of 5 API keys reached. Please delete an inactive key to generate a new one.'
      }
    }

    // 4. Generate random API key
    const fullApiKey = generateSecureApiKey()

    // 5. Hash the API key
    const keyHash = hashApiKey(fullApiKey)

    // 6. Insert into database
    const { data: insertedKey, error: insertError } = await supabase
      .from('api_keys')
      .insert({
        organization_id: organizationId,
        key_hash: keyHash,
        created_by_user_id: user.id,
        is_active: true
      })
      .select('id')
      .single()

    if (insertError || !insertedKey) {
      return { success: false, error: 'Failed to create API key' }
    }

    // Revalidate the API keys page
    revalidatePath('/api-keys')

    // 7. Return the FULL API key (not the hash) - shown only once
    return {
      success: true,
      apiKey: fullApiKey,
      keyId: insertedKey.id
    }

  } catch (error) {
    console.error('Error generating API key:', error)
    return { success: false, error: 'An unexpected error occurred' }
  }
}

/**
 * Server Action: Delete (soft delete) an API key
 */
export async function deleteApiKey(keyId: number): Promise<ActionResult<Record<string, never>>> {
  try {
    const supabase = await createClient()

    // 1. Get authenticated user
    const { data: { user }, error: userError } = await supabase.auth.getUser()

    if (userError || !user) {
      return { success: false, error: 'Not authenticated' }
    }

    // 2. Get user's organization
    const { data: membership, error: membershipError } = await supabase
      .from('organization_members')
      .select('organization_id')
      .eq('user_id', user.id)
      .single()

    if (membershipError || !membership) {
      return { success: false, error: 'No organization found for user' }
    }

    // 3. Verify the API key belongs to the user's organization
    const { data: apiKey, error: fetchError } = await supabase
      .from('api_keys')
      .select('organization_id')
      .eq('id', keyId)
      .single()

    if (fetchError || !apiKey) {
      return { success: false, error: 'API key not found' }
    }

    if (apiKey.organization_id !== membership.organization_id) {
      return { success: false, error: 'Unauthorized: API key does not belong to your organization' }
    }

    // 4. Soft delete: Set is_active = false
    const { error: updateError } = await supabase
      .from('api_keys')
      .update({ is_active: false })
      .eq('id', keyId)

    if (updateError) {
      return { success: false, error: 'Failed to delete API key' }
    }

    // Revalidate the API keys page
    revalidatePath('/api-keys')

    return { success: true }

  } catch (error) {
    console.error('Error deleting API key:', error)
    return { success: false, error: 'An unexpected error occurred' }
  }
}

/**
 * Server Action: Regenerate an API key (mark old as inactive, create new one)
 */
export async function regenerateApiKey(keyId: number): Promise<ActionResult<{ apiKey: string; keyId: number }>> {
  try {
    const supabase = await createClient()

    // 1. Get authenticated user
    const { data: { user }, error: userError } = await supabase.auth.getUser()

    if (userError || !user) {
      return { success: false, error: 'Not authenticated' }
    }

    // 2. Get user's organization
    const { data: membership, error: membershipError } = await supabase
      .from('organization_members')
      .select('organization_id')
      .eq('user_id', user.id)
      .single()

    if (membershipError || !membership) {
      return { success: false, error: 'No organization found for user' }
    }

    const organizationId = membership.organization_id

    // 3. Verify the API key belongs to the user's organization
    const { data: oldKey, error: fetchError } = await supabase
      .from('api_keys')
      .select('organization_id')
      .eq('id', keyId)
      .single()

    if (fetchError || !oldKey) {
      return { success: false, error: 'API key not found' }
    }

    if (oldKey.organization_id !== organizationId) {
      return { success: false, error: 'Unauthorized: API key does not belong to your organization' }
    }

    // 4. Mark old key as inactive
    const { error: deactivateError } = await supabase
      .from('api_keys')
      .update({ is_active: false })
      .eq('id', keyId)

    if (deactivateError) {
      return { success: false, error: 'Failed to deactivate old API key' }
    }

    // 5. Generate new random API key
    const fullApiKey = generateSecureApiKey()

    // 6. Hash the new API key
    const keyHash = hashApiKey(fullApiKey)

    // 7. Insert new key into database
    const { data: newKey, error: insertError } = await supabase
      .from('api_keys')
      .insert({
        organization_id: organizationId,
        key_hash: keyHash,
        created_by_user_id: user.id,
        is_active: true
      })
      .select('id')
      .single()

    if (insertError || !newKey) {
      return { success: false, error: 'Failed to create new API key' }
    }

    // Revalidate the API keys page
    revalidatePath('/api-keys')

    // 8. Return the FULL new API key (not the hash) - shown only once
    return {
      success: true,
      apiKey: fullApiKey,
      keyId: newKey.id
    }

  } catch (error) {
    console.error('Error regenerating API key:', error)
    return { success: false, error: 'An unexpected error occurred' }
  }
}
