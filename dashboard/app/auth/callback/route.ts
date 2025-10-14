import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'
import { createOrganization } from '@/app/(auth)/actions'

/**
 * Auth Callback Route Handler
 *
 * Handles the OAuth callback from Supabase Auth (e.g., email confirmation, magic links)
 * Exchanges the authorization code for a session and redirects to the dashboard
 */
export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const next = requestUrl.searchParams.get('next') ?? '/'

  if (code) {
    const supabase = await createClient()

    // Exchange the code for a session
    const { data, error } = await supabase.auth.exchangeCodeForSession(code)

    if (error) {
      console.error('Error exchanging code for session:', error)
      return NextResponse.redirect(new URL(`/login?error=${encodeURIComponent(error.message)}`, requestUrl.origin))
    }

    // Create organization for new users (T020)
    if (data.user) {
      // Check if organization already exists
      const { data: existing } = await supabase
        .from('organization_members')
        .select('organization_id')
        .eq('user_id', data.user.id)
        .single()

      if (!existing) {
        // Create organization for new user
        await createOrganization(data.user.id, data.user.email!)
      }
    }
  }

  // Redirect to the dashboard or specified next URL
  return NextResponse.redirect(new URL(next, requestUrl.origin))
}
