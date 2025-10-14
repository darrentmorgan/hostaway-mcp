/**
 * Billing calculation utilities for the dashboard
 * Handles pricing, prorations, and billing period calculations
 */

/**
 * Pricing configuration (can be moved to environment variables)
 */
export const PRICING = {
  pricePerListing: 5.0, // $5 per listing per month
  currency: 'USD',
  currencySymbol: '$',
} as const

/**
 * Calculate monthly bill based on listing count
 * @param listingCount - Number of active listings
 * @returns Projected monthly bill
 */
export function calculateMonthlyBill(listingCount: number): number {
  return listingCount * PRICING.pricePerListing
}

/**
 * Calculate prorated bill for remaining days in period
 * @param listingCount - Number of active listings
 * @param daysRemaining - Days remaining in billing period
 * @param daysInPeriod - Total days in billing period (default 30)
 * @returns Prorated bill amount
 */
export function calculateProratedBill(
  listingCount: number,
  daysRemaining: number,
  daysInPeriod: number = 30
): number {
  const fullMonthBill = calculateMonthlyBill(listingCount)
  return (fullMonthBill * daysRemaining) / daysInPeriod
}

/**
 * Format currency amount with symbol
 * @param amount - Amount in dollars
 * @param includeCents - Whether to include cents (default true)
 * @returns Formatted currency string (e.g., "$25.00")
 */
export function formatCurrency(
  amount: number,
  includeCents: boolean = true
): string {
  return `${PRICING.currencySymbol}${includeCents ? amount.toFixed(2) : Math.floor(amount).toString()}`
}

/**
 * Calculate the change in bill between two listing counts
 * @param oldCount - Previous listing count
 * @param newCount - New listing count
 * @returns Object with change amount and percentage
 */
export function calculateBillChange(
  oldCount: number,
  newCount: number
): { amount: number; percentage: number; isIncrease: boolean } {
  const oldBill = calculateMonthlyBill(oldCount)
  const newBill = calculateMonthlyBill(newCount)
  const amount = newBill - oldBill
  const percentage = oldBill > 0 ? (amount / oldBill) * 100 : 0

  return {
    amount,
    percentage,
    isIncrease: amount > 0,
  }
}

/**
 * Get days remaining in current billing period (assumes monthly billing on 1st)
 * @returns Number of days remaining
 */
export function getDaysRemainingInPeriod(): number {
  const now = new Date()
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  const diffTime = lastDay.getTime() - now.getTime()
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

/**
 * Get total days in current billing period
 * @returns Number of days in period
 */
export function getDaysInPeriod(): number {
  const now = new Date()
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  return lastDay.getDate()
}

/**
 * Calculate usage-based costs (if API request limits are implemented)
 * @param apiRequests - Number of API requests
 * @param includedRequests - Number of included requests (default 10000)
 * @param pricePerExtraRequest - Price per additional request (default $0.001)
 * @returns Overage cost
 */
export function calculateUsageOverage(
  apiRequests: number,
  includedRequests: number = 10000,
  pricePerExtraRequest: number = 0.001
): number {
  const overage = Math.max(0, apiRequests - includedRequests)
  return overage * pricePerExtraRequest
}

/**
 * Format change percentage with sign
 * @param percentage - Percentage value
 * @returns Formatted percentage string (e.g., "+15.2%")
 */
export function formatPercentageChange(percentage: number): string {
  const sign = percentage > 0 ? '+' : ''
  return `${sign}${percentage.toFixed(1)}%`
}
