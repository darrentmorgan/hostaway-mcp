'use client'

import { useState } from 'react'
import { Tables } from '@/lib/types/database'
import APIKeyGenerateModal from './APIKeyGenerateModal'
import { generateApiKey, deleteApiKey, regenerateApiKey } from '@/app/dashboard/api-keys/actions'

type ApiKey = Tables<'api_keys'>

interface APIKeyListProps {
  keys: ApiKey[]
  maxKeysReached: boolean
}

/**
 * Formats the key hash for display (masking)
 * Shows first 6 chars + "..." + last 6 chars
 */
function maskKeyHash(keyHash: string): string {
  if (keyHash.length <= 12) return keyHash
  const prefix = keyHash.substring(0, 6)
  const suffix = keyHash.substring(keyHash.length - 6)
  return `${prefix}...${suffix}`
}

/**
 * Formats a date string for display
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Component to display list of API keys with actions
 */
export default function APIKeyList({ keys, maxKeysReached }: APIKeyListProps) {
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false)
  const [deletingKeyId, setDeletingKeyId] = useState<number | null>(null)
  const [regeneratingKeyId, setRegeneratingKeyId] = useState<number | null>(null)
  const [keyToRegenerate, setKeyToRegenerate] = useState<number | null>(null)

  const handleGenerate = async () => {
    const result = await generateApiKey()
    return result
  }

  const handleDelete = async (keyId: number) => {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return
    }

    setDeletingKeyId(keyId)
    const result = await deleteApiKey(keyId)
    setDeletingKeyId(null)

    if (!result.success) {
      alert(`Error: ${result.error}`)
    }
  }

  const handleRegenerateClick = (keyId: number) => {
    if (confirm('Are you sure you want to regenerate this API key? The old key will stop working immediately.')) {
      setKeyToRegenerate(keyId)
      setIsGenerateModalOpen(true)
    }
  }

  const handleRegenerateInModal = async () => {
    if (!keyToRegenerate) return { success: false, error: 'No key selected' }

    const result = await regenerateApiKey(keyToRegenerate)
    setKeyToRegenerate(null)
    return result
  }

  const handleModalClose = () => {
    setIsGenerateModalOpen(false)
    setKeyToRegenerate(null)
  }

  return (
    <>
      {/* Generate Button */}
      <div className="mb-6">
        <button
          onClick={() => setIsGenerateModalOpen(true)}
          disabled={maxKeysReached}
          className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
            maxKeysReached
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
          }`}
        >
          <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Generate New Key
        </button>
      </div>

      {/* API Keys List */}
      {keys.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No API keys</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by generating your first API key.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {keys.map((key) => (
            <div
              key={key.id}
              className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="px-6 py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    {/* Masked Key */}
                    <div className="flex items-center space-x-3">
                      <code className="text-sm font-mono text-gray-900 bg-gray-100 px-3 py-1 rounded">
                        {maskKeyHash(key.key_hash)}
                      </code>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          key.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {key.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>

                    {/* Metadata */}
                    <div className="mt-3 flex flex-col sm:flex-row sm:space-x-6 text-sm text-gray-500">
                      <div className="flex items-center">
                        <svg className="h-4 w-4 mr-1.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        Created: {formatDate(key.created_at)}
                      </div>
                      <div className="flex items-center mt-1 sm:mt-0">
                        <svg className="h-4 w-4 mr-1.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Last used: {key.last_used_at ? formatDate(key.last_used_at) : 'Never'}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  {key.is_active && (
                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => handleRegenerateClick(key.id)}
                        disabled={regeneratingKeyId === key.id}
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                      >
                        {regeneratingKeyId === key.id ? (
                          <>
                            <div className="animate-spin h-3 w-3 mr-1.5 border-b-2 border-gray-700 rounded-full"></div>
                            Regenerating...
                          </>
                        ) : (
                          <>
                            <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            Regenerate
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => handleDelete(key.id)}
                        disabled={deletingKeyId === key.id}
                        className="inline-flex items-center px-3 py-1.5 border border-red-300 text-xs font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                      >
                        {deletingKeyId === key.id ? (
                          <>
                            <div className="animate-spin h-3 w-3 mr-1.5 border-b-2 border-red-700 rounded-full"></div>
                            Deleting...
                          </>
                        ) : (
                          <>
                            <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            Delete
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Generate/Regenerate Modal */}
      <APIKeyGenerateModal
        isOpen={isGenerateModalOpen}
        onClose={handleModalClose}
        onGenerate={keyToRegenerate ? handleRegenerateInModal : handleGenerate}
      />
    </>
  )
}
