import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import HostawayCredentials from '@/components/settings/HostawayCredentials'

export default async function SettingsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  // Get organization and credentials
  const { data: membership } = await supabase
    .from('organization_members')
    .select('organization_id')
    .eq('user_id', user.id)
    .single()

  let credentials = null
  if (membership) {
    const { data } = await supabase
      .from('hostaway_credentials')
      .select('account_id, credentials_valid, last_validated_at')
      .eq('organization_id', membership.organization_id)
      .single()
    credentials = data
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Hostaway Connection</h2>
        <HostawayCredentials initialCredentials={credentials} />
      </div>
    </div>
  )
}
