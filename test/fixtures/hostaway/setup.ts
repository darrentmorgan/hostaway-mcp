/**
 * Hostaway API mocking infrastructure using nock
 *
 * Provides mock HTTP responses for:
 * - Authentication (POST /v1/accessTokens)
 * - Listings/properties (GET /v1/listings)
 * - Bookings (GET /v1/reservations)
 * - Financial reports (GET /v1/financialReports)
 * - Pagination responses
 * - Error scenarios (500 HTML, 429 rate limits)
 */

import nock from 'nock';
import { generateProperties, generateBookings, generateLargeFinancialReport, generateLargeHtmlError } from '../generators/index.js';

const HOSTAWAY_API_BASE = 'https://api.hostaway.com';

/**
 * Setup basic Hostaway API authentication mock
 *
 * Mocks successful OAuth token response
 */
export function setupAuthMock(): nock.Scope {
  return nock(HOSTAWAY_API_BASE)
    .post('/v1/accessTokens')
    .reply(200, {
      access_token: 'mock_access_token_12345',
      token_type: 'Bearer',
      expires_in: 3600,
    })
    .persist(); // Keep this mock active for all tests
}

export interface ListingsMockOptions {
  /** Total number of properties to mock */
  total?: number;
  /** Page size (limit parameter) */
  limit?: number;
  /** Current offset */
  offset?: number;
}

/**
 * Setup listings/properties endpoint mock with pagination support
 *
 * @param options - Mock configuration options
 */
export function setupListingsMock(options: ListingsMockOptions = {}): nock.Scope {
  const {
    total = 100,
    limit = 50,
    offset = 0,
  } = options;

  const properties = generateProperties(total);
  const page = properties.slice(offset, offset + limit);
  const hasMore = offset + limit < total;

  return nock(HOSTAWAY_API_BASE)
    .get('/v1/listings')
    .query(true)  // Match any query parameters
    .reply(200, (uri, requestBody) => {
      // Parse query parameters from the URI
      const url = new URL(uri, HOSTAWAY_API_BASE);
      const queryLimit = parseInt(url.searchParams.get('limit') || String(limit), 10);
      const queryOffset = parseInt(url.searchParams.get('offset') || '0', 10);

      // Return page based on actual query params
      const responsePage = properties.slice(queryOffset, queryOffset + queryLimit);
      const responseHasMore = queryOffset + queryLimit < total;

      return {
        status: 'success',
        result: responsePage,
        count: responsePage.length,
        limit: queryLimit,
        offset: queryOffset,
        hasMore: responseHasMore,
        nextCursor: responseHasMore ? Buffer.from(JSON.stringify({ offset: queryOffset + queryLimit })).toString('base64') : undefined,
      };
    })
    .persist();
}

export interface BookingsMockOptions {
  /** Total number of bookings to mock */
  total?: number;
  /** Page size (limit parameter) */
  limit?: number;
  /** Current offset */
  offset?: number;
}

/**
 * Setup bookings/reservations endpoint mock with pagination support
 *
 * @param options - Mock configuration options
 */
export function setupBookingsMock(options: BookingsMockOptions = {}): nock.Scope {
  const {
    total = 100,
    limit = 50,
    offset = 0,
  } = options;

  const bookings = generateBookings(total);
  const page = bookings.slice(offset, offset + limit);
  const hasMore = offset + limit < total;

  return nock(HOSTAWAY_API_BASE)
    .get('/v1/reservations')
    .query(true)  // Match any query parameters
    .reply(200, (uri, requestBody) => {
      // Parse query parameters from the URI
      const url = new URL(uri, HOSTAWAY_API_BASE);
      const queryLimit = parseInt(url.searchParams.get('limit') || String(limit), 10);
      const queryOffset = parseInt(url.searchParams.get('offset') || '0', 10);

      // Return page based on actual query params
      const responsePage = bookings.slice(queryOffset, queryOffset + queryLimit);
      const responseHasMore = queryOffset + queryLimit < total;

      return {
        status: 'success',
        result: responsePage,
        count: responsePage.length,
        limit: queryLimit,
        offset: queryOffset,
        hasMore: responseHasMore,
        nextCursor: responseHasMore ? Buffer.from(JSON.stringify({ offset: queryOffset + queryLimit })).toString('base64') : undefined,
      };
    })
    .persist();
}

/**
 * Setup large financial report mock (triggers preview mode)
 *
 * Returns an oversized financial report that should trigger
 * preview/summarization in the MCP server.
 */
export function setupLargeFinancialReportMock(): nock.Scope {
  const largeReport = generateLargeFinancialReport();

  return nock(HOSTAWAY_API_BASE)
    .get('/v1/financialReports')
    .query(true) // Match any query parameters
    .reply(200, largeReport);
}

/**
 * Setup error mocks for testing error hygiene
 *
 * Includes:
 * - 500 Internal Server Error with large HTML body
 * - 429 Rate Limit with Retry-After header
 * - 403 Forbidden
 * - 404 Not Found
 */
export function setupErrorMocks(): void {
  // 500 error with large HTML body (should be stripped by MCP server)
  nock(HOSTAWAY_API_BASE)
    .get('/v1/listings')
    .query({ trigger_error: '500' })
    .reply(500, generateLargeHtmlError(), {
      'Content-Type': 'text/html',
    });

  // 429 rate limit with Retry-After header
  nock(HOSTAWAY_API_BASE)
    .get('/v1/listings')
    .query({ trigger_error: '429' })
    .reply(429, {
      error: 'Rate limit exceeded',
      message: 'Too many requests. Please retry after the specified time.',
    }, {
      'Retry-After': '60',
      'X-RateLimit-Limit': '1000',
      'X-RateLimit-Remaining': '0',
      'X-RateLimit-Reset': String(Date.now() + 60000),
    });

  // 403 forbidden
  nock(HOSTAWAY_API_BASE)
    .get('/v1/financialReports')
    .query({ trigger_error: '403' })
    .reply(403, {
      error: 'Forbidden',
      message: 'Your account does not have permission to access financial reports.',
    });

  // 404 not found
  nock(HOSTAWAY_API_BASE)
    .get('/v1/listings/999999')
    .reply(404, {
      error: 'Not found',
      message: 'Property not found.',
    });
}

/**
 * Setup all common Hostaway API mocks
 *
 * Convenience function to set up authentication, listings, bookings, and error mocks.
 */
export function setupHostawayMocks(options: {
  listings?: ListingsMockOptions;
  bookings?: BookingsMockOptions;
  includeErrors?: boolean;
} = {}): void {
  setupAuthMock();

  if (options.listings !== undefined) {
    setupListingsMock(options.listings);
  }

  if (options.bookings !== undefined) {
    setupBookingsMock(options.bookings);
  }

  if (options.includeErrors) {
    setupErrorMocks();
  }
}

/**
 * Clear all nock mocks
 *
 * Call this in test cleanup to ensure mocks don't leak between tests.
 */
export function clearHostawayMocks(): void {
  nock.cleanAll();
}

/**
 * Verify all expected nock mocks were called
 *
 * Call this at the end of tests to ensure expected HTTP calls were made.
 */
export function verifyHostawayMocks(): void {
  if (!nock.isDone()) {
    const pending = nock.pendingMocks();
    throw new Error(`Pending mocks not called: ${pending.join(', ')}`);
  }
}
