/**
 * Error handling utilities with correlation ID support
 */

import { nanoid } from 'nanoid'

/**
 * Generate a correlation ID for request tracking
 */
export function generateCorrelationId(): string {
  return nanoid(10)
}

/**
 * Log error with correlation ID and context
 */
export function logError(
  message: string,
  error: unknown,
  context?: Record<string, unknown>
): string {
  const correlationId = generateCorrelationId()

  console.error(JSON.stringify({
    correlationId,
    message,
    error: error instanceof Error ? {
      message: error.message,
      stack: error.stack,
      name: error.name,
    } : error,
    context,
    timestamp: new Date().toISOString(),
  }))

  return correlationId
}

/**
 * Standard error messages for consistent UX
 */
export const ErrorMessages = {
  // Authentication errors
  NOT_AUTHENTICATED: 'You must be signed in to perform this action.',
  ORGANIZATION_NOT_FOUND: 'No organization found for your account. Please contact support.',
  ORGANIZATION_LOAD_FAILED: 'Failed to load your organization details. Please try again.',

  // Hostaway errors
  HOSTAWAY_AUTH_FAILED: 'Failed to authenticate with Hostaway. Please check your credentials.',
  HOSTAWAY_CONNECTION_FAILED: 'Failed to connect to Hostaway. Please try again.',
  HOSTAWAY_NO_CREDENTIALS: 'No Hostaway credentials found. Please connect your account first.',
  HOSTAWAY_INVALID_CREDENTIALS: 'Invalid Hostaway credentials. Please reconnect your account.',

  // Database errors
  DATABASE_ERROR: 'A database error occurred. Please try again.',
  CREDENTIALS_SAVE_FAILED: 'Failed to save your credentials. Please try again.',

  // Stripe errors
  STRIPE_NOT_CONFIGURED: 'Billing is not configured. Please contact support.',
  STRIPE_CUSTOMER_NOT_FOUND: 'No billing account found. Please contact support.',
  STRIPE_SESSION_FAILED: 'Failed to create billing session. Please try again.',

  // Generic errors
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again or contact support.',
} as const

/**
 * Format error response with correlation ID
 */
export function createErrorResponse(
  message: string,
  correlationId: string
): { success: false; error: string; correlationId: string } {
  return {
    success: false,
    error: message,
    correlationId,
  }
}

/**
 * Format success response with optional warning
 */
export function createSuccessResponse<T extends Record<string, unknown>>(
  data: T,
  warning?: string
): { success: true } & T & { warning?: string } {
  return {
    success: true,
    ...data,
    ...(warning && { warning }),
  }
}
