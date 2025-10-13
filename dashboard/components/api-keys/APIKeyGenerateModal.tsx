'use client'

import { Fragment, useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import APIKeyDisplay from './APIKeyDisplay'

interface APIKeyGenerateModalProps {
  isOpen: boolean
  onClose: () => void
  onGenerate: () => Promise<{ success: boolean; apiKey?: string; error?: string }>
}

type ModalState = 'initial' | 'generating' | 'success' | 'error'

/**
 * Modal for generating new API keys
 * Shows the full API key only once with security warnings
 */
export default function APIKeyGenerateModal({
  isOpen,
  onClose,
  onGenerate
}: APIKeyGenerateModalProps) {
  const [state, setState] = useState<ModalState>('initial')
  const [apiKey, setApiKey] = useState<string>('')
  const [error, setError] = useState<string>('')

  const handleGenerate = async () => {
    setState('generating')
    setError('')

    try {
      const result = await onGenerate()

      if (result.success && result.apiKey) {
        setApiKey(result.apiKey)
        setState('success')
      } else {
        setError(result.error || 'Failed to generate API key')
        setState('error')
      }
    } catch (err) {
      setError('An unexpected error occurred')
      setState('error')
    }
  }

  const handleClose = () => {
    // Reset state when closing
    setState('initial')
    setApiKey('')
    setError('')
    onClose()
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <Dialog.Title
                  as="h3"
                  className="text-lg font-medium leading-6 text-gray-900"
                >
                  {state === 'success' ? 'API Key Generated' : 'Generate New API Key'}
                </Dialog.Title>

                <div className="mt-4">
                  {/* Initial State */}
                  {state === 'initial' && (
                    <div className="space-y-4">
                      <p className="text-sm text-gray-500">
                        Generate a new API key for authenticating requests to the Hostaway MCP Server.
                        This key will be shown only once, so make sure to copy and save it securely.
                      </p>
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <p className="text-sm text-yellow-800">
                          <strong>Important:</strong> The API key will be displayed only once.
                          You won't be able to view it again after closing this dialog.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Generating State */}
                  {state === 'generating' && (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                      <span className="ml-3 text-sm text-gray-500">Generating API key...</span>
                    </div>
                  )}

                  {/* Success State */}
                  {state === 'success' && (
                    <div className="space-y-4">
                      <p className="text-sm text-gray-500 mb-4">
                        Your API key has been generated successfully. Copy it now and store it in a secure location.
                      </p>
                      <APIKeyDisplay apiKey={apiKey} />
                    </div>
                  )}

                  {/* Error State */}
                  {state === 'error' && (
                    <div className="space-y-4">
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div className="flex">
                          <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                          </div>
                          <div className="ml-3">
                            <h3 className="text-sm font-medium text-red-800">Error</h3>
                            <p className="mt-1 text-sm text-red-700">{error}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Actions */}
                <div className="mt-6 flex justify-end space-x-3">
                  {state === 'initial' && (
                    <>
                      <button
                        type="button"
                        className="inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        onClick={handleClose}
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        className="inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        onClick={handleGenerate}
                      >
                        Generate Key
                      </button>
                    </>
                  )}

                  {(state === 'success' || state === 'error') && (
                    <button
                      type="button"
                      className="inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                      onClick={handleClose}
                    >
                      {state === 'success' ? "I've saved my key" : 'Close'}
                    </button>
                  )}
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
