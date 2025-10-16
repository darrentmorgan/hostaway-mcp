'use client'
import { useState } from 'react'
import { connectHostaway, disconnectHostaway, refreshHostawayConnection } from '@/app/dashboard/settings/actions'

interface HostawayCredential {
  account_id: string
  last_validated_at: string
}

interface Props {
  initialCredentials: HostawayCredential | null
}

export default function HostawayCredentials({ initialCredentials }: Props) {
  const [accountId, setAccountId] = useState('')
  const [secretKey, setSecretKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [listingCount, setListingCount] = useState<number | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess(false)
    setListingCount(null)

    const result = await connectHostaway(accountId, secretKey)

    if (result.success) {
      setSuccess(true)
      setListingCount(result.listingCount || null)
      setAccountId('')
      setSecretKey('')
      // Refresh the page to show updated credentials
      setTimeout(() => {
        window.location.reload()
      }, 2000)
    } else {
      setError(result.error || 'Failed to connect')
    }
    setLoading(false)
  }

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect your Hostaway account?')) {
      return
    }

    setDisconnecting(true)
    setError('')

    const result = await disconnectHostaway()

    if (result.success) {
      window.location.reload()
    } else {
      setError(result.error || 'Failed to disconnect')
    }
    setDisconnecting(false)
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    setError('')
    setSuccess(false)
    setListingCount(null)

    const result = await refreshHostawayConnection()

    if (result.success) {
      setSuccess(true)
      setListingCount('listingCount' in result ? result.listingCount : null)
      setTimeout(() => {
        window.location.reload()
      }, 2000)
    } else {
      setError(result.error || 'Failed to refresh connection')
    }
    setRefreshing(false)
  }

  return (
    <div>
      {initialCredentials ? (
        <div className="mb-4 p-4 bg-green-50 rounded border border-green-200">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-green-800 font-medium">Connected: {initialCredentials.account_id}</p>
              <p className="text-sm text-green-600">Last validated: {new Date(initialCredentials.last_validated_at).toLocaleDateString()}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleRefresh}
                disabled={refreshing || disconnecting}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </button>
              <button
                onClick={handleDisconnect}
                disabled={disconnecting || refreshing}
                className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                {disconnecting ? 'Disconnecting...' : 'Disconnect'}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <p className="text-gray-600 mb-4">No Hostaway account connected</p>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <div className="p-4 bg-red-50 text-red-700 rounded">{error}</div>}
        {success && (
          <div className="p-4 bg-green-50 text-green-700 rounded">
            <p className="font-medium">Credentials saved successfully!</p>
            {listingCount !== null && (
              <p className="text-sm mt-1">
                Found {listingCount} listing{listingCount !== 1 ? 's' : ''} in your Hostaway account
              </p>
            )}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-2">Hostaway Account ID</label>
          <input
            type="text"
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            required
            disabled={loading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Secret Key</label>
          <input
            type="password"
            value={secretKey}
            onChange={(e) => setSecretKey(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            required
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Connecting...' : 'Connect Hostaway Account'}
        </button>
      </form>
    </div>
  )
}
