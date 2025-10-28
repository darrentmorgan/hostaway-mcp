/**
 * Global test setup for overflow-safety test suite
 *
 * Runs once before all tests to configure environment and utilities
 */

import { afterAll, beforeAll } from 'vitest';

// Default environment variables for testing
const DEFAULT_ENV = {
  MCP_OUTPUT_TOKEN_THRESHOLD: '50000',
  MCP_OUTPUT_TOKEN_HARD_CAP: '100000',
  MCP_DEFAULT_PAGE_SIZE: '50',
  HOSTAWAY_API_BASE_URL: 'https://api.hostaway.com',
  // Dummy credentials for testing (nock mocks HTTP requests)
  HOSTAWAY_ACCOUNT_ID: 'test_account_id',
  HOSTAWAY_SECRET_KEY: 'test_secret_key',
};

beforeAll(() => {
  // Set default environment variables if not already set
  for (const [key, value] of Object.entries(DEFAULT_ENV)) {
    if (!process.env[key]) {
      process.env[key] = value;
    }
  }

  // Log test configuration
  console.log('Test environment configured:');
  console.log(`  Token threshold: ${process.env.MCP_OUTPUT_TOKEN_THRESHOLD}`);
  console.log(`  Token hard cap: ${process.env.MCP_OUTPUT_TOKEN_HARD_CAP}`);
  console.log(`  Default page size: ${process.env.MCP_DEFAULT_PAGE_SIZE}`);
});

afterAll(() => {
  // Cleanup if needed
});
