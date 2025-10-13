'use client'

import { useState } from 'react'

interface HostawayCredentialsProps {
  isConnected: boolean
  accountId?: string
  lastValidated?: string | null
  onConnect: (accountId: string, secretKey: string) => Promise<void>
  onDisconnect?: () => Promise<void>
}

export default function HostawayCredentials({
  isConnected,
  accountId: initialAccountId,
  lastValidated,
  onConnect,
  onDisconnect,
}: HostawayCredentialsProps) {
  const [accountId, setAccountId] = useState('')
  const [secretKey, setSecretKey] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(!isConnected)

  const validateForm = () => {
    if (!accountId || !secretKey) {
      setError('Both Account ID and Secret Key are required')
      return false
    }

    // Basic account ID format validation (alphanumeric and underscores)
    if (!/^[a-zA-Z0-9_-]+$/.test(accountId)) {
      setError('Account ID can only contain letters, numbers, hyphens, and underscores')
      return false
    }

    if (secretKey.length < 10) {
      setError('Secret Key must be at least 10 characters long')
      return false
    }

    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!validateForm()) {
      return
    }

    setLoading(true)

    try {
      await onConnect(accountId, secretKey)
      // Clear the form after successful connection
      setAccountId('')
      setSecretKey('')
      setShowForm(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect Hostaway account')
      console.error('Connection error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDisconnect = async () => {
    if (!onDisconnect) return

    setLoading(true)
    setError(null)

    try {
      await onDisconnect()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect Hostaway account')
      console.error('Disconnect error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Hostaway Integration</h3>
            <p className="mt-1 text-sm text-gray-500">
              Connect your Hostaway account to enable API access
            </p>
          </div>
          {isConnected && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              <svg
                className="w-4 h-4 mr-1.5"
                fill="currentColor"
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                  clipRule="evenodd"
                />
              </svg>
              Connected
            </span>
          )}
        </div>
      </div>

      {isConnected && !showForm ? (
        <div className="space-y-4">
          <div className="bg-gray-50 rounded-md p-4">
            <dl className="space-y-2">
              <div className="flex justify-between">
                <dt className="text-sm font-medium text-gray-500">Account ID</dt>
                <dd className="text-sm text-gray-900 font-mono">{initialAccountId}</dd>
              </div>
              {lastValidated && (
                <div className="flex justify-between">
                  <dt className="text-sm font-medium text-gray-500">Last Validated</dt>
                  <dd className="text-sm text-gray-900">
                    {new Date(lastValidated).toLocaleString()}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={() => setShowForm(true)}
              className="flex-1 bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Update Credentials
            </button>
            {onDisconnect && (
              <button
                type="button"
                onClick={handleDisconnect}
                disabled={loading}
                className="flex-1 bg-red-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Disconnecting...' : 'Disconnect'}
              </button>
            )}
          </div>
        </div>
      ) : (
        <>
          <div className="mb-4 bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-blue-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h4 className="text-sm font-medium text-blue-800">How to find your Hostaway credentials</h4>
                <div className="mt-2 text-sm text-blue-700">
                  <ol className="list-decimal list-inside space-y-1">
                    <li>Log in to your Hostaway account</li>
                    <li>Navigate to Settings → API Access</li>
                    <li>Copy your Account ID and Secret Key</li>
                    <li>Paste them into the form below</li>
                  </ol>
                </div>
              </div>
            </div>
          </div>

          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">{error}</h3>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="accountId" className="block text-sm font-medium text-gray-700 mb-1">
                Hostaway Account ID
              </label>
              <input
                id="accountId"
                name="accountId"
                type="text"
                required
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="your-account-id"
                disabled={loading}
              />
              <p className="mt-1 text-xs text-gray-500">
                Your unique Hostaway account identifier
              </p>
            </div>

            <div>
              <label htmlFor="secretKey" className="block text-sm font-medium text-gray-700 mb-1">
                Hostaway Secret Key
              </label>
              <input
                id="secretKey"
                name="secretKey"
                type="password"
                required
                value={secretKey}
                onChange={(e) => setSecretKey(e.target.value)}
                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm font-mono"
                placeholder="••••••••••••••••"
                disabled={loading}
              />
              <p className="mt-1 text-xs text-gray-500">
                Your secret API key (stored encrypted)
              </p>
            </div>

            <div className="flex space-x-3">
              {isConnected && (
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false)
                    setError(null)
                    setAccountId('')
                    setSecretKey('')
                  }}
                  className="flex-1 bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Cancel
                </button>
              )}
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-blue-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Connecting...' : isConnected ? 'Update Connection' : 'Connect Account'}
              </button>
            </div>
          </form>
        </>
      )}
    </div>
  )
}
