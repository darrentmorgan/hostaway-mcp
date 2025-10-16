import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import APIKeyList from '@/components/api-keys/APIKeyList'
import ClaudeDesktopSetup from '@/components/api-keys/ClaudeDesktopSetup'
import { Tables } from '@/lib/types/database'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

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

  if (keysError && keysError.code !== 'PGRST116') {
    // PGRST116 = no rows returned, which is fine for users without API keys yet
    console.error('Error fetching API keys:', keysError)
    throw new Error('Failed to load API keys')
  }

  const keys = apiKeys || []
  const activeKeyCount = keys.filter(k => k.is_active).length

  // Get the most recent active key for the setup guide
  const mostRecentActiveKey = keys.find(k => k.is_active)
  const serverUrl = process.env.NEXT_PUBLIC_MCP_SERVER_URL || 'https://your-server.com'

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">API Keys</h1>
        <p className="mt-2 text-muted-foreground">
          Manage your MCP API keys for authenticating requests to the Hostaway
          MCP Server. Keys are used in your Claude Desktop configuration.
        </p>
      </div>

      {/* Maximum Keys Warning */}
      {activeKeyCount >= 5 && (
        <Alert variant="destructive">
          <AlertTitle>Maximum Limit Reached</AlertTitle>
          <AlertDescription>
            You have {activeKeyCount} active API keys. Please delete an
            inactive key before generating a new one.
          </AlertDescription>
        </Alert>
      )}

      {/* API Keys List */}
      <APIKeyList keys={keys} maxKeysReached={activeKeyCount >= 5} />

      {/* Claude Desktop Setup Guide */}
      <ClaudeDesktopSetup
        apiKey={mostRecentActiveKey?.key_hash || null}
        serverUrl={serverUrl}
      />

      {/* Security Notice */}
      <Alert>
        <AlertTitle>Security Best Practices</AlertTitle>
        <AlertDescription>
          <ul className="mt-2 space-y-1 list-disc list-inside">
            <li>
              API keys are shown only once when generated. Store them securely.
            </li>
            <li>
              Never share your API keys or commit them to version control.
            </li>
            <li>
              Regenerate keys immediately if they may have been compromised.
            </li>
            <li>Inactive keys cannot be used for authentication.</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  )
}
