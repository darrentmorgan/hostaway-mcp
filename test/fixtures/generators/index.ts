/**
 * Fixture generators index
 *
 * Central export point for all fixture generators
 */

export { generateProperty, generateProperties, type Property } from './properties.js';
export { generateBooking, generateBookings, type Booking } from './bookings.js';
export {
  generateFinancialReport,
  generateLargeFinancialReport,
  type FinancialReport,
} from './financial.js';
export { generateLargeHtmlError, generateCompactJsonError } from './errors.js';
