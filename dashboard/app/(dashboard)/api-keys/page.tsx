import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import APIKeyList from '@/components/api-keys/APIKeyList'
import { Tables } from '@/lib/types/database'

type ApiKey = Tables<'api_keys'>

export default async function ApiKeysPage() {
  const supabase = await createClient()

  // Check if user is authenticated
  const { data: { user }, error: userError } = await supabase.auth.getUser()

  if (userError || !user) {
    redirect('/login')
  }

  // Get user's organization membership
  const { data: membership, error: membershipError } = await supabase
    .from('organization_members')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  if (membershipError || !membership) {
    redirect('/login')
  }

  // Fetch organization's API keys (both active and inactive)
  const { data: apiKeys, error: keysError } = await supabase
    .from('api_keys')
    .select('*')
    .eq('organization_id', membership.organization_id)
    .order('created_at', { ascending: false })

  if (keysError) {
    console.error('Error fetching API keys:', keysError)
  }

  const keys = apiKeys || []
  const activeKeyCount = keys.filter(k => k.is_active).length

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Page Header */}
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-3xl font-bold text-gray-900">API Keys</h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage your MCP API keys for authenticating requests to the Hostaway MCP Server.
            Keys are used in your Claude Desktop configuration.
          </p>
          {activeKeyCount >= 5 && (
            <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-yellow-700">
                    <strong>Maximum limit reached:</strong> You have {activeKeyCount} active API keys.
                    Please delete an inactive key before generating a new one.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* API Keys List */}
      <div className="mt-8">
        <APIKeyList keys={keys} maxKeysReached={activeKeyCount >= 5} />
      </div>

      {/* Security Notice */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">Security Best Practices</h3>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>API keys are shown only once when generated. Store them securely.</li>
          <li>Never share your API keys or commit them to version control.</li>
          <li>Regenerate keys immediately if they may have been compromised.</li>
          <li>Inactive keys cannot be used for authentication.</li>
        </ul>
      </div>
    </div>
  )
}
