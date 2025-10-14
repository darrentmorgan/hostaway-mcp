'use client'
import { useState } from 'react'
import { connectHostaway } from '@/app/(dashboard)/settings/actions'

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
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const result = await connectHostaway(accountId, secretKey)

    if (result.success) {
      setSuccess(true)
      setAccountId('')
      setSecretKey('')
    } else {
      setError(result.error || 'Failed to connect')
    }
    setLoading(false)
  }

  return (
    <div>
      {initialCredentials ? (
        <div className="mb-4 p-4 bg-green-50 rounded">
          <p className="text-green-800">Connected: {initialCredentials.account_id}</p>
          <p className="text-sm text-green-600">Last validated: {new Date(initialCredentials.last_validated_at).toLocaleDateString()}</p>
        </div>
      ) : (
        <p className="text-gray-600 mb-4">No Hostaway account connected</p>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <div className="p-4 bg-red-50 text-red-700 rounded">{error}</div>}
        {success && <div className="p-4 bg-green-50 text-green-700 rounded">Credentials saved successfully!</div>}

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
