import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import HostawayCredentials from '@/components/settings/HostawayCredentials'

// Server Action for connecting Hostaway credentials
async function connectHostaway(accountId: string, secretKey: string) {
  'use server'

  const supabase = await createClient()

  // Get current user
  const { data: { user }, error: userError } = await supabase.auth.getUser()

  if (userError || !user) {
    throw new Error('Unauthorized')
  }

  // Get user's organization
  const { data: membership, error: membershipError } = await supabase
    .from('organization_members')
    .select('organization_id, role')
    .eq('user_id', user.id)
    .single()

  if (membershipError || !membership) {
    throw new Error('No organization found for user')
  }

  // Only owners and admins can update credentials
  if (membership.role !== 'owner' && membership.role !== 'admin') {
    throw new Error('Insufficient permissions. Only owners and admins can update credentials.')
  }

  // Validate credentials with Hostaway API
  try {
    const response = await fetch('https://api.hostaway.com/v1/listings', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${secretKey}`,
        'X-Account-Id': accountId,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Invalid Hostaway credentials. Please check your Account ID and Secret Key.')
      }
      throw new Error(`Hostaway API error: ${response.statusText}`)
    }

    // API call successful, credentials are valid
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Credential validation failed: ${error.message}`)
    }
    throw new Error('Failed to validate credentials with Hostaway API')
  }

  // Check if credentials already exist
  const { data: existing, error: checkError } = await supabase
    .from('hostaway_credentials')
    .select('id')
    .eq('organization_id', membership.organization_id)
    .single()

  if (checkError && checkError.code !== 'PGRST116') {
    throw new Error('Failed to check existing credentials')
  }

  // Use Supabase function to encrypt the secret key
  const { data: encryptedData, error: encryptError } = await supabase
    .rpc('encrypt_hostaway_credential', { plain_secret: secretKey })

  if (encryptError) {
    throw new Error('Failed to encrypt secret key')
  }

  if (existing) {
    // Update existing credentials
    const { error: updateError } = await supabase
      .from('hostaway_credentials')
      .update({
        account_id: accountId,
        encrypted_secret_key: encryptedData,
        credentials_valid: true,
        last_validated_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      .eq('id', existing.id)

    if (updateError) {
      throw new Error('Failed to update credentials')
    }
  } else {
    // Insert new credentials
    const { error: insertError } = await supabase
      .from('hostaway_credentials')
      .insert({
        organization_id: membership.organization_id,
        account_id: accountId,
        encrypted_secret_key: encryptedData,
        credentials_valid: true,
        last_validated_at: new Date().toISOString(),
      })

    if (insertError) {
      throw new Error('Failed to save credentials')
    }
  }

  // Revalidate the page to show updated credentials
  // Return void to match the onConnect prop type
}

export default async function SettingsPage() {
  const supabase = await createClient()

  // Check if user is authenticated
  const { data: { user }, error: userError } = await supabase.auth.getUser()

  if (userError || !user) {
    redirect('/login')
  }

  // Get user's organization
  const { data: membership, error: membershipError } = await supabase
    .from('organization_members')
    .select('organization_id, role')
    .eq('user_id', user.id)
    .single()

  if (membershipError) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <p className="text-sm text-yellow-800">
              You are not a member of any organization. Please contact your administrator.
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Get Hostaway credentials for the organization
  const { data: credentials, error: credentialsError } = await supabase
    .from('hostaway_credentials')
    .select('account_id, credentials_valid, last_validated_at')
    .eq('organization_id', membership.organization_id)
    .single()

  const isConnected = !!credentials && credentials.credentials_valid

  // Client-side wrapper for the server action
  async function handleConnect(accountId: string, secretKey: string) {
    'use server'
    await connectHostaway(accountId, secretKey)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage your Hostaway integration and account settings
          </p>
        </div>

        <div className="space-y-6">
          {/* User Info Card */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Account Information</h3>
            <dl className="space-y-2">
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">Email</dt>
                <dd className="text-sm text-gray-900">{user.email}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">Role</dt>
                <dd className="text-sm text-gray-900 capitalize">{membership.role}</dd>
              </div>
            </dl>
          </div>

          {/* Hostaway Credentials Component */}
          <HostawayCredentials
            isConnected={isConnected}
            accountId={credentials?.account_id}
            lastValidated={credentials?.last_validated_at}
            onConnect={handleConnect}
          />

          {credentialsError && credentialsError.code !== 'PGRST116' && (
            <div className="rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">
                Error loading credentials: {credentialsError.message}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
