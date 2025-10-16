import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

/**
 * Auth Signout Route Handler
 *
 * Handles user signout by clearing the Supabase session
 * and redirecting to the login page
 */
export async function POST(request: Request) {
  const requestUrl = new URL(request.url)
  const supabase = await createClient()

  // Sign out the user
  const { error } = await supabase.auth.signOut()

  if (error) {
    console.error('Error signing out:', error)
    return NextResponse.redirect(
      new URL(`/dashboard?error=${encodeURIComponent(error.message)}`, requestUrl.origin)
    )
  }

  // Redirect to login page after successful signout
  return NextResponse.redirect(new URL('/login', requestUrl.origin))
}
