'use server'
import { createClient } from '@/lib/supabase/server'

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

  // TODO: Validate credentials with Hostaway API test call
  // For now, just store them
  const { error } = await supabase
    .from('hostaway_credentials')
    .upsert({
      organization_id: membership.organization_id,
      account_id: accountId,
      encrypted_secret_key: secretKey, // TODO: Encrypt with Vault
      credentials_valid: true,
      last_validated_at: new Date().toISOString(),
    })

  if (error) return { success: false, error: error.message }
  return { success: true }
}
