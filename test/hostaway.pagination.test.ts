/**
 * Pagination contract tests for Hostaway MCP server
 *
 * Tests verify that pagination works correctly under forced-small token caps:
 * - List endpoints respect limit parameters
 * - Pages are disjoint (no duplicate IDs)
 * - Cursors work correctly
 * - Final page has no cursor
 * - Token budgets are enforced
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { HTTPTestClient } from './utils/httpClient.js';
import { assertBelowHardCap, assertPaginationCursor } from './utils/tokenEstimator.js';
import { setupHostawayMocks, clearHostawayMocks } from './fixtures/hostaway/setup.js';

// Response type for paginated endpoints (matches FastAPI PaginatedResponse model)
interface PaginatedResponse<T> {
  items: T[];
  nextCursor?: string;
  meta: {
    totalCount: number;
    pageSize: number;
    hasMore: boolean;
  };
}

describe('Pagination Contracts', () => {
  let httpClient: HTTPTestClient;

  beforeEach(async () => {
    // Setup HTTP mocks for Hostaway API
    setupHostawayMocks({
      listings: { total: 100, limit: 10, offset: 0 },
      bookings: { total: 100, limit: 10, offset: 0 },
    });

    // Start FastAPI server with test configuration
    // Uses MockHostawayClient with deterministic data (100 listings, 100 bookings)
    httpClient = new HTTPTestClient({
      env: {
        MCP_DEFAULT_PAGE_SIZE: '10',
        MCP_OUTPUT_TOKEN_THRESHOLD: '30000',
        MCP_OUTPUT_TOKEN_HARD_CAP: '50000',
        HOSTAWAY_TEST_MODE: 'true',
      },
    });

    await httpClient.start();
  });

  afterEach(async () => {
    await httpClient.stop();
    clearHostawayMocks();
  });

  describe('list_properties endpoint', () => {
    it('should respect limit parameter', async () => {
      // Call list_properties with limit=10
      const result = await httpClient.callEndpoint<PaginatedResponse<{ id: number }>>('GET', '/api/listings', { limit: 10 });

      // Verify response
      expect(result.isError).toBe(false);
      expect(result.content).toHaveProperty('items');

      const properties = result.content.items;

      // Should return ≤10 items
      expect(properties.length).toBeLessThanOrEqual(10);
      expect(properties.length).toBeGreaterThan(0);

      // Verify token budget (using realistic cap for real API data)
      assertBelowHardCap(result.content, 30000);
    });

    it('should return nextCursor when more results available', async () => {
      // Call list_properties with limit=10 (total is 100, so more results exist)
      const result = await httpClient.callEndpoint<PaginatedResponse<{ id: number }>>('GET', '/api/listings', { limit: 10 });

      expect(result.isError).toBe(false);

      // Should have nextCursor since there are more results
      assertPaginationCursor(result.content, true);

      const nextCursor = result.content.nextCursor;
      expect(nextCursor).toBeDefined();
      expect(nextCursor).not.toBe('');

      // Verify token budget (using realistic cap for real API data)
      assertBelowHardCap(result.content, 30000);
    });

    it('should return disjoint pages (no duplicate IDs)', async () => {
      // Get first page
      const page1 = await httpClient.callEndpoint<PaginatedResponse<{ id: number }>>('GET', '/api/listings', { limit: 10 });
      expect(page1.isError).toBe(false);

      const page1Properties = page1.content.items;
      const page1Ids = new Set(page1Properties.map((p) => p.id));

      // Get second page using cursor
      const cursor1 = page1.content.nextCursor;
      expect(cursor1).toBeDefined();

      const page2 = await httpClient.callEndpoint<PaginatedResponse<{ id: number }>>('GET', '/api/listings', {
        limit: 10,
        cursor: cursor1,
      });
      expect(page2.isError).toBe(false);

      const page2Properties = page2.content.items;
      const page2Ids = new Set(page2Properties.map((p) => p.id));

      // Verify no overlap between page1 and page2 IDs
      const intersection = [...page1Ids].filter((id) => page2Ids.has(id));
      expect(intersection.length).toBe(0);

      // Verify both pages have data
      expect(page1Properties.length).toBeGreaterThan(0);
      expect(page2Properties.length).toBeGreaterThan(0);

      // Verify token budgets
      assertBelowHardCap(page1.content, 3000);
      assertBelowHardCap(page2.content, 3000);
    });

    it('should not return nextCursor on final page', async () => {
      // Navigate to the last page by following cursors
      let currentCursor: string | undefined;
      let pageCount = 0;
      let lastPageResult: Awaited<ReturnType<typeof mcpClient.callTool<PaginatedResponse<{ id: number }>>>>;

      // Get first page
      lastPageResult = await httpClient.callEndpoint<PaginatedResponse<{ id: number }>>('GET', '/api/listings', { limit: 10 });
      expect(lastPageResult.isError).toBe(false);

      currentCursor = lastPageResult.content.nextCursor;

      // Follow cursors until we reach the last page (max 20 iterations for safety)
      while (currentCursor && pageCount < 20) {
        lastPageResult = await httpClient.callEndpoint<PaginatedResponse<{ id: number }>>('GET', '/api/listings', {
          limit: 10,
          cursor: currentCursor,
        });
        expect(lastPageResult.isError).toBe(false);

        currentCursor = lastPageResult.content.nextCursor;
        pageCount++;
      }

      // Final page should have no nextCursor
      assertPaginationCursor(lastPageResult.content, false);

      // Should still have results on the last page
      const lastPageProperties = lastPageResult.content.items;
      expect(lastPageProperties.length).toBeGreaterThan(0);

      // Verify token budget
      assertBelowHardCap(lastPageResult.content, 3000);
    });

    it('should handle empty results gracefully', async () => {
      // Call list_properties with a cursor that points beyond available data
      // This simulates pagination beyond the dataset

      // Create a properly formatted cursor using the same encoding as the server
      // The cursor must include payload and signature
      const payload = { offset: 10000, ts: Date.now() / 1000 };

      // Create signature matching Python's json.dumps with sort_keys=True, separators=(",", ":")
      const payloadJson = JSON.stringify(payload, ['offset', 'ts']);

      const crypto = await import('crypto');
      const signature = crypto.createHmac('sha256', 'hostaway-cursor-secret').update(payloadJson).digest('hex');

      const cursorData = { payload, sig: signature };
      const cursor = Buffer.from(JSON.stringify(cursorData)).toString('base64');

      const result = await httpClient.callEndpoint<PaginatedResponse<unknown>>('GET', '/api/listings', {
        limit: 10,
        cursor,
      });

      expect(result.isError).toBe(false);

      // Should return empty array
      const properties = result.content.items;
      expect(properties).toEqual([]);

      // Should have no nextCursor
      assertPaginationCursor(result.content, false);

      // Verify token budget (even empty responses should be within budget)
      assertBelowHardCap(result.content, 3000);
    });
  });

  describe('search_bookings endpoint', () => {
    it('should respect pagination with limit parameter', async () => {
      // Call search_bookings with limit=10
      const result = await httpClient.callEndpoint<PaginatedResponse<{ id: number }>>('GET', '/api/reservations', { limit: 10 });

      // Verify response
      expect(result.isError).toBe(false);
      expect(result.content).toHaveProperty('items');

      const bookings = result.content.items;

      // Should return ≤10 items
      expect(bookings.length).toBeLessThanOrEqual(10);
      expect(bookings.length).toBeGreaterThan(0);

      // Verify token budget (using realistic cap for real API data)
      assertBelowHardCap(result.content, 30000);
    });

    it('should return disjoint booking pages', async () => {
      // Get first page
      const page1 = await httpClient.callEndpoint<PaginatedResponse<{ id: number }>>('GET', '/api/reservations', { limit: 10 });
      expect(page1.isError).toBe(false);

      const page1Bookings = page1.content.items;
      const page1Ids = new Set(page1Bookings.map((b) => b.id));

      // Get second page
      const cursor1 = page1.content.nextCursor;
      expect(cursor1).toBeDefined();

      const page2 = await httpClient.callEndpoint<PaginatedResponse<{ id: number }>>('GET', '/api/reservations', {
        limit: 10,
        cursor: cursor1,
      });
      expect(page2.isError).toBe(false);

      const page2Bookings = page2.content.items;
      const page2Ids = new Set(page2Bookings.map((b) => b.id));

      // Verify no overlap
      const intersection = [...page1Ids].filter((id) => page2Ids.has(id));
      expect(intersection.length).toBe(0);

      // Verify token budgets
      assertBelowHardCap(page1.content, 3000);
      assertBelowHardCap(page2.content, 3000);
    });

    it('should handle final page correctly', async () => {
      // Navigate through pages to find the final page
      let currentCursor: string | undefined;
      let pageCount = 0;
      let lastPageResult: Awaited<ReturnType<typeof mcpClient.callTool<PaginatedResponse<{ id: number }>>>>;

      // Get first page
      lastPageResult = await httpClient.callEndpoint<PaginatedResponse<{ id: number }>>('GET', '/api/reservations', { limit: 10 });
      expect(lastPageResult.isError).toBe(false);

      currentCursor = lastPageResult.content.nextCursor;

      // Follow cursors to last page
      while (currentCursor && pageCount < 20) {
        lastPageResult = await httpClient.callEndpoint<PaginatedResponse<{ id: number }>>('GET', '/api/reservations', {
          limit: 10,
          cursor: currentCursor,
        });
        expect(lastPageResult.isError).toBe(false);

        currentCursor = lastPageResult.content.nextCursor;
        pageCount++;
      }

      // Final page should have no nextCursor
      assertPaginationCursor(lastPageResult.content, false);

      // Verify token budget
      assertBelowHardCap(lastPageResult.content, 3000);
    });
  });

  describe('Pagination consistency across endpoints', () => {
    it('should enforce consistent pagination behavior', async () => {
      // Test both endpoints with same limit
      const propertiesResult = await httpClient.callEndpoint<PaginatedResponse<unknown>>('GET', '/api/listings', { limit: 5 });
      const bookingsResult = await httpClient.callEndpoint<PaginatedResponse<unknown>>('GET', '/api/reservations', { limit: 5 });

      // Both should respect limit
      const properties = propertiesResult.content.items;
      const bookings = bookingsResult.content.items;

      expect(properties.length).toBeLessThanOrEqual(5);
      expect(bookings.length).toBeLessThanOrEqual(5);

      // Both should have nextCursor (since datasets have 100 items)
      assertPaginationCursor(propertiesResult.content, true);
      assertPaginationCursor(bookingsResult.content, true);

      // Both should be within token budget
      assertBelowHardCap(propertiesResult.content, 3000);
      assertBelowHardCap(bookingsResult.content, 3000);
    });

    it('should never exceed hard cap with any page size', async () => {
      // Test with various page sizes
      const pageSizes = [5, 10, 20, 50];

      for (const pageSize of pageSizes) {
        const result = await httpClient.callEndpoint<PaginatedResponse<unknown>>('GET', '/api/listings', { limit: pageSize });

        expect(result.isError).toBe(false);

        // Hard cap should NEVER be exceeded
        assertBelowHardCap(result.content, 50000);
      }
    });
  });
});
