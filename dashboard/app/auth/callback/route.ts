import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/navigation'
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
      const { data: existing, error: memberError } = await supabase
        .from('organization_members')
        .select('organization_id')
        .eq('user_id', data.user.id)
        .single()

      if (memberError && memberError.code !== 'PGRST116') {
        // PGRST116 = no rows returned, which is expected for new users
        console.error('Error checking organization membership:', memberError)
        return NextResponse.redirect(
          new URL(`/login?error=${encodeURIComponent('Failed to verify organization membership')}`, requestUrl.origin)
        )
      }

      if (!existing) {
        // Validate email exists
        if (!data.user.email) {
          console.error('User authenticated without email:', data.user.id)
          // Sign out user to prevent broken state
          await supabase.auth.signOut()
          return NextResponse.redirect(
            new URL(`/signup?error=${encodeURIComponent('Email address is required to create an account.')}`, requestUrl.origin)
          )
        }

        // Create organization for new user
        try {
          await createOrganization(data.user.id, data.user.email)
        } catch (orgError) {
          console.error('Error creating organization for user:', data.user.id, orgError)
          // Sign out user to prevent broken state (user without organization)
          await supabase.auth.signOut()
          return NextResponse.redirect(
            new URL(`/signup?error=${encodeURIComponent('Account created but organization setup failed. Please try signing up again or contact support.')}`, requestUrl.origin)
          )
        }
      }
    }
  }

  // Redirect to the dashboard or specified next URL
  return NextResponse.redirect(new URL(next, requestUrl.origin))
}
