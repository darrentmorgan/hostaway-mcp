import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl w-full space-y-8 text-center">
        <div>
          <h1 className="text-5xl font-extrabold text-gray-900 sm:text-6xl md:text-7xl">
            Hostaway MCP Server
          </h1>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Multi-tenant billable MCP server for AI-powered property management automation
          </p>
        </div>

        <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/signup"
            className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 md:py-4 md:text-lg md:px-10 transition-colors"
          >
            Get Started
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10 transition-colors"
          >
            Sign In
          </Link>
        </div>

        <div className="mt-12 grid gap-8 md:grid-cols-3">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-blue-600 text-3xl mb-4">🔐</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Secure Authentication</h3>
            <p className="text-gray-600">
              Multi-tenant architecture with organization-level data isolation and encrypted credentials
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-blue-600 text-3xl mb-4">🔑</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">API Key Management</h3>
            <p className="text-gray-600">
              Generate secure API keys for MCP clients with usage tracking and access control
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-blue-600 text-3xl mb-4">🏠</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Hostaway Integration</h3>
            <p className="text-gray-600">
              Connect your Hostaway account and enable AI-powered property management automation
            </p>
          </div>
        </div>

        <div className="mt-8 text-sm text-gray-500">
          <p>Enterprise-grade property management automation platform</p>
          <p className="mt-1">Built with Supabase, Next.js, and FastAPI</p>
        </div>
      </div>
    </div>
  )
}
