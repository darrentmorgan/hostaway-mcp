import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

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
    const { error } = await supabase.auth.exchangeCodeForSession(code)

    if (error) {
      console.error('Error exchanging code for session:', error)
      // Redirect to login with error message
      return NextResponse.redirect(new URL(`/login?error=${encodeURIComponent(error.message)}`, requestUrl.origin))
    }
  }

  // Redirect to the dashboard or specified next URL
  return NextResponse.redirect(new URL(next, requestUrl.origin))
}
