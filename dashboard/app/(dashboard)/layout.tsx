import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { DashboardNav, DashboardHeader } from '@/components/dashboard-nav'
import { DynamicBreadcrumb } from '@/components/DynamicBreadcrumb'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="hidden w-64 flex-col border-r bg-card md:flex">
        <div className="flex h-16 items-center border-b px-6">
          <h2 className="text-lg font-semibold">Navigation</h2>
        </div>
        <DashboardNav />
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <DashboardHeader userEmail={user.email} />

        {/* Breadcrumb navigation */}
        <div className="border-b bg-background px-6 py-3">
          <DynamicBreadcrumb />
        </div>

        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  )
}
