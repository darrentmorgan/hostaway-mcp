'use server'

import { createClient } from '@/lib/supabase/server'
import { createServiceRoleClient } from '@/lib/supabase/service-role'

/**
 * Create organization and organization member after user signup
 * This runs with service role permissions to bypass RLS policies
 */
export async function createOrganization(userId: string, userEmail: string) {
  try {
    const supabase = createServiceRoleClient()

    // Extract organization name from email domain
    const emailDomain = userEmail.split('@')[1]
    const orgName = emailDomain.split('.')[0].charAt(0).toUpperCase() + emailDomain.split('.')[0].slice(1)

    // 1. Create organization
    const { data: organization, error: orgError } = await supabase
      .from('organizations')
      .insert({
        name: `${orgName} Organization`,
        owner_user_id: userId,
      })
      .select()
      .single()

    if (orgError) {
      console.error('Error creating organization:', orgError)
      throw new Error('Failed to create organization')
    }

    // 2. Create organization member (owner role)
    const { error: memberError } = await supabase
      .from('organization_members')
      .insert({
        organization_id: organization.id,
        user_id: userId,
        role: 'owner',
      })

    if (memberError) {
      console.error('Error creating organization member:', memberError)
      // Rollback: delete the organization
      await supabase.from('organizations').delete().eq('id', organization.id)
      throw new Error('Failed to create organization member')
    }

    return {
      success: true,
      organizationId: organization.id,
      organizationName: organization.name,
    }
  } catch (error) {
    console.error('Organization creation error:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    }
  }
}
