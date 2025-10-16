import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import HostawayCredentials from '@/components/settings/HostawayCredentials'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export default async function SettingsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  // Get organization and credentials
  const { data: membership, error: memberError } = await supabase
    .from('organization_members')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  if (memberError) {
    console.error('Error fetching organization membership:', memberError)
    throw new Error('Failed to load organization membership')
  }

  let credentials = null
  if (membership) {
    const { data, error: credError } = await supabase
      .from('hostaway_credentials')
      .select('account_id, credentials_valid, last_validated_at')
      .eq('organization_id', membership.organization_id)
      .single()

    if (credError && credError.code !== 'PGRST116') {
      // PGRST116 = no rows returned, which is fine for users without credentials yet
      console.error('Error fetching Hostaway credentials:', credError)
      throw new Error('Failed to load Hostaway credentials')
    }

    credentials = data
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="mt-2 text-muted-foreground">
          Manage your account and integration settings
        </p>
      </div>

      {/* Hostaway Connection Card */}
      <Card>
        <CardHeader>
          <CardTitle>Hostaway Connection</CardTitle>
          <CardDescription>
            Configure your Hostaway credentials to sync listings and data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <HostawayCredentials initialCredentials={credentials} />
        </CardContent>
      </Card>
    </div>
  )
}
