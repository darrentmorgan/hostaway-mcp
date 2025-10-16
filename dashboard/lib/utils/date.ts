/**
 * Date utility functions for the dashboard
 * Handles date formatting, calculations, and conversions
 */

/**
 * Get the current month in YYYY-MM format for usage metrics
 * @returns Current month string (e.g., "2025-10")
 */
export function getCurrentMonth(): string {
  return new Date().toISOString().substring(0, 7)
}

/**
 * Get a date N months ago in YYYY-MM format
 * @param monthsAgo - Number of months to go back
 * @returns Month string (e.g., "2025-08")
 */
export function getMonthsAgo(monthsAgo: number): string {
  const date = new Date()
  date.setMonth(date.getMonth() - monthsAgo)
  return date.toISOString().substring(0, 7)
}

/**
 * Get a date N days ago
 * @param daysAgo - Number of days to go back
 * @returns Date object
 */
export function getDaysAgo(daysAgo: number): Date {
  const date = new Date()
  date.setDate(date.getDate() - daysAgo)
  return date
}

/**
 * Format a YYYY-MM month string to human-readable format
 * @param monthYear - Month in YYYY-MM format (e.g., "2025-10")
 * @returns Formatted month string (e.g., "Oct 2025")
 */
export function formatMonthYear(monthYear: string): string {
  const date = new Date(monthYear + '-01')
  return date.toLocaleDateString('en-US', {
    month: 'short',
    year: 'numeric',
  })
}

/**
 * Format a date to human-readable format
 * @param date - Date string or Date object
 * @returns Formatted date string (e.g., "Oct 14, 2025")
 */
export function formatDate(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return dateObj.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

/**
 * Format a date to relative time (e.g., "2 days ago")
 * @param date - Date string or Date object
 * @returns Relative time string
 */
export function formatRelativeTime(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffMs = now.getTime() - dateObj.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 60) return 'just now'
  if (diffMin < 60) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`
  if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`
  if (diffDay < 30) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`

  return formatDate(dateObj)
}

/**
 * Get the start and end dates for the current billing period
 * @returns Object with start and end dates
 */
export function getCurrentBillingPeriod(): { start: Date; end: Date } {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth(), 1)
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59)

  return { start, end }
}

/**
 * Get an array of month strings for the last N months
 * @param months - Number of months to include
 * @returns Array of month strings in YYYY-MM format
 */
export function getLastNMonths(months: number): string[] {
  const result: string[] = []
  for (let i = 0; i < months; i++) {
    result.push(getMonthsAgo(i))
  }
  return result.reverse()
}
