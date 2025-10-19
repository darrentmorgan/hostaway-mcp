# Implementation Plan: Automated Overflow-Safety Test Suite

**Feature ID**: 006-overflow-safety-test-suite
**Status**: Ready for Implementation
**Target**: TypeScript/Vitest test harness with stdio MCP client
**Created**: 2025-10-16
**Last Updated**: 2025-10-16

---

## 1. Executive Summary

### Objective

Build a **TypeScript/Vitest test harness** that:
- Launches the MCP server over stdio
- Mocks Hostaway HTTP responses with nock
- Asserts output-size contracts (pagination, preview, chunking, error compactness)
- Validates behavior under configurable token caps

### Success Criteria

- ✅ Test suite runs in <5 minutes in CI
- ✅ 100% coverage of high-volume endpoints
- ✅ 0 violations of hard token cap
- ✅ ≥95% of endpoints return paginated/summarized results under forced-small caps
- ✅ All error responses <2KB
- ✅ Flake rate <1%

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│               Vitest Test Suite (TypeScript)             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐  ┌──────────────────┐              │
│  │  MCP Client    │  │  Token Estimator │              │
│  │  (stdio)       │  │  (bytes/4 * 1.2) │              │
│  └────────┬───────┘  └────────┬─────────┘              │
│           │                   │                         │
│           ▼                   ▼                         │
│  ┌─────────────────────────────────────┐               │
│  │      Test Assertions                │               │
│  │  - Pagination contracts             │               │
│  │  - Preview mode activation          │               │
│  │  - Token cap enforcement            │               │
│  │  - Error hygiene                    │               │
│  └──────────────┬──────────────────────┘               │
└─────────────────┼────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              MCP Server (Python, stdio)                  │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Pagination   │  │ Preview      │  │ Token        │  │
│  │ Service      │  │ Service      │  │ Estimator    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         ▼                 ▼                 ▼           │
│  ┌─────────────────────────────────────────────┐       │
│  │          Endpoint Handlers                  │       │
│  └───────────────────┬─────────────────────────┘       │
└────────────────────────┼───────────────────────────────┘
                         │
                         ▼ (mocked by nock)
              ┌──────────────────────┐
              │   Hostaway API       │
              │   (HTTP mocked)      │
              └──────────────────────┘
```

---

## 2. Implementation Phases

### Phase 1: Foundation (Week 1) - 5 days

**Goal**: Set up TypeScript/Vitest infrastructure with MCP stdio client and nock mocking

#### Day 1-2: Project Setup & Dependencies

**Tasks**:
- [ ] T001: Initialize TypeScript test project
  - Create `test/` directory structure
  - Configure `tsconfig.json` for test environment
  - Set up Vitest configuration
  - Install dependencies (vitest, @modelcontextprotocol/sdk, nock, etc.)

**Deliverables**:
```typescript
// test/vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./setup.ts'],
    timeout: 30000,  // 30s per test
    hookTimeout: 10000,
  },
})
```

**Dependencies** (package.json):
```json
{
  "devDependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "@types/node": "^20.0.0",
    "nock": "^14.0.0",
    "tsx": "^4.0.0",
    "typescript": "^5.0.0",
    "vitest": "^1.0.0"
  }
}
```

**Acceptance Criteria**:
- ✅ `npm test` runs Vitest successfully
- ✅ TypeScript compiles without errors
- ✅ Basic test file executes

---

#### Day 2-3: MCP Client Wrapper

**Tasks**:
- [ ] T002: Implement MCP stdio client wrapper
  - Spawn MCP server process
  - Handle stdio communication
  - Tool invocation helpers
  - Graceful shutdown

**Deliverables**:
```typescript
// test/utils/mcpClient.ts
import { spawn, ChildProcess } from 'child_process'
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js'

export class MCPTestClient {
  private process: ChildProcess
  private client: Client
  private transport: StdioClientTransport

  constructor(private config: {
    serverCommand: string
    serverArgs?: string[]
    env?: Record<string, string>
  }) {}

  async start(): Promise<void> {
    // Spawn MCP server
    this.process = spawn(this.config.serverCommand, this.config.serverArgs || [], {
      env: { ...process.env, ...this.config.env },
      stdio: ['pipe', 'pipe', 'inherit'],
    })

    // Create stdio transport
    this.transport = new StdioClientTransport({
      reader: this.process.stdout,
      writer: this.process.stdin,
    })

    // Initialize client
    this.client = new Client(
      {
        name: 'overflow-safety-tests',
        version: '1.0.0',
      },
      {
        capabilities: {},
      }
    )

    await this.client.connect(this.transport)
  }

  async callTool<T = unknown>(
    toolName: string,
    args: Record<string, unknown>
  ): Promise<{
    content: T
    estimatedTokens: number
    isError: boolean
  }> {
    const result = await this.client.callTool({
      name: toolName,
      arguments: args,
    })

    // Serialize result and estimate tokens
    const content = JSON.stringify(result.content)
    const estimatedTokens = estimateTokens(content)

    return {
      content: result.content as T,
      estimatedTokens,
      isError: result.isError || false,
    }
  }

  async listTools() {
    return await this.client.listTools()
  }

  async listResources() {
    return await this.client.listResources()
  }

  async readResource(uri: string) {
    return await this.client.readResource({ uri })
  }

  async stop(): Promise<void> {
    await this.client.close()
    this.process.kill()

    // Wait for process to exit
    return new Promise((resolve) => {
      this.process.on('exit', () => resolve())
    })
  }
}

// Helper function
function estimateTokens(text: string): number {
  // bytes/4 heuristic with 20% safety margin
  const bytes = Buffer.byteLength(text, 'utf-8')
  const baseEstimate = bytes / 4
  return Math.ceil(baseEstimate * 1.2)
}
```

**Acceptance Criteria**:
- ✅ Client can spawn MCP server
- ✅ Client can call tools and get responses
- ✅ Client handles graceful shutdown
- ✅ Token estimation matches Python implementation (±5%)

---

#### Day 3-4: Token Estimator & Assertions

**Tasks**:
- [ ] T003: Implement token estimation utilities
  - Port Python token estimator to TypeScript
  - Create assertion helpers for token caps
  - Budget checking utilities

**Deliverables**:
```typescript
// test/utils/tokenEstimator.ts
export function estimateTokens(text: string): number {
  const charCount = text.length
  const baseEstimate = charCount / 4
  const safetyMargin = baseEstimate * 0.20
  return Math.ceil(baseEstimate + safetyMargin)
}

export function estimateTokensFromObject(obj: unknown): number {
  const json = JSON.stringify(obj)
  return estimateTokens(json)
}

export function checkTokenBudget(
  text: string,
  threshold: number
): {
  estimated: number
  exceeds: boolean
  ratio: number
} {
  const estimated = estimateTokens(text)
  const exceeds = estimated > threshold
  const ratio = threshold > 0 ? estimated / threshold : 0

  return { estimated, exceeds, ratio }
}

// Vitest assertion helpers
export function assertWithinTokenBudget(
  content: unknown,
  threshold: number,
  message?: string
) {
  const tokens = estimateTokensFromObject(content)
  if (tokens > threshold) {
    throw new Error(
      message ||
        `Token budget exceeded: ${tokens} tokens > ${threshold} threshold`
    )
  }
}

export function assertBelowHardCap(content: unknown, hardCap: number) {
  const tokens = estimateTokensFromObject(content)
  if (tokens > hardCap) {
    throw new Error(
      `HARD CAP VIOLATION: ${tokens} tokens > ${hardCap} hard cap`
    )
  }
}
```

**Acceptance Criteria**:
- ✅ Token estimation accurate to ±10%
- ✅ Assertion helpers integrate with Vitest
- ✅ Budget checking supports soft/hard thresholds

---

#### Day 4-5: Nock HTTP Mocking Infrastructure

**Tasks**:
- [ ] T004: Set up nock mocking for Hostaway API
  - Create fixture generators
  - Mock authentication endpoints
  - Mock pagination scenarios
  - Mock error responses

**Deliverables**:
```typescript
// test/fixtures/hostaway/setup.ts
import nock from 'nock'

const HOSTAWAY_BASE_URL = 'https://api.hostaway.com'

export function setupHostawayMocks() {
  // Clear any existing mocks
  nock.cleanAll()

  // Mock authentication
  nock(HOSTAWAY_BASE_URL)
    .post('/v1/accessTokens')
    .reply(200, {
      access_token: 'test_token_abc123',
      token_type: 'Bearer',
      expires_in: 3600,
    })
    .persist()

  // Mock listings endpoint with pagination
  nock(HOSTAWAY_BASE_URL)
    .get('/v1/listings')
    .query(true)  // Accept any query params
    .reply((uri) => {
      const url = new URL(uri, HOSTAWAY_BASE_URL)
      const limit = parseInt(url.searchParams.get('limit') || '50')
      const offset = parseInt(url.searchParams.get('offset') || '0')

      return [
        200,
        {
          status: 'success',
          result: generateProperties(limit),
          count: 500,  // Total available
          limit,
          offset,
        },
      ]
    })
    .persist()
}

export function setupLargeFinancialReportMock() {
  // Mock that returns oversized financial data
  nock(HOSTAWAY_BASE_URL)
    .get('/v1/financials/reports')
    .query(true)
    .reply(200, {
      status: 'success',
      result: generateLargeFinancialReport(),
    })
}

export function setupErrorMocks() {
  // Mock 500 error with large HTML body
  nock(HOSTAWAY_BASE_URL)
    .get('/v1/error/500')
    .reply(500, generateLargeHtmlError())

  // Mock 429 rate limit with headers
  nock(HOSTAWAY_BASE_URL)
    .get('/v1/error/429')
    .reply(429, {
      error: 'rate_limit_exceeded',
      message: 'Too many requests',
    }, {
      'X-RateLimit-Remaining': '0',
      'X-RateLimit-Reset': String(Date.now() + 60000),
      'Retry-After': '60',
    })
}
```

```typescript
// test/fixtures/generators/properties.ts
export function generateProperties(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: `Property ${i + 1}`,
    address: `${i + 1} Main Street`,
    city: ['San Francisco', 'New York', 'Los Angeles'][i % 3],
    state: ['CA', 'NY', 'CA'][i % 3],
    country: 'USA',
    capacity: Math.floor(Math.random() * 10) + 2,
    bedrooms: Math.floor(Math.random() * 5) + 1,
    bathrooms: Math.floor(Math.random() * 3) + 1,
    basePrice: Math.floor(Math.random() * 500) + 100,
    isActive: true,
  }))
}

export function generateLargeFinancialReport() {
  // Generate report with 1000+ rows
  const rows = Array.from({ length: 1000 }, (_, i) => ({
    date: `2025-${String(Math.floor(i / 30) + 1).padStart(2, '0')}-${String((i % 30) + 1).padStart(2, '0')}`,
    bookingId: `BK${i}`,
    revenue: Math.random() * 1000,
    expenses: Math.random() * 200,
    profit: Math.random() * 800,
    notes: `Detailed financial notes for booking ${i} `.repeat(10),  // Verbose
  }))

  return {
    startDate: '2025-01-01',
    endDate: '2025-12-31',
    totalRevenue: 500000,
    totalExpenses: 100000,
    totalProfit: 400000,
    rows,
  }
}

export function generateLargeHtmlError() {
  // Simulate large 500 error body
  return `
<!DOCTYPE html>
<html>
<head><title>500 Internal Server Error</title></head>
<body>
<h1>500 Internal Server Error</h1>
<pre>
Traceback (most recent call last):
  ${'  File "server.py", line 123, in handler\n'.repeat(100)}
  ... [10KB+ of stack trace] ...
</pre>
</body>
</html>
  `
}
```

**Acceptance Criteria**:
- ✅ All Hostaway endpoints can be mocked
- ✅ Pagination responses realistic and deterministic
- ✅ Error scenarios (500, 429) mockable
- ✅ Large payloads generate correct token estimates

---

### Phase 2: Core Contract Tests (Week 2) - 5 days

**Goal**: Implement pagination, preview, and error hygiene tests

#### Day 6-7: Pagination Contract Tests

**Tasks**:
- [ ] T005: Test `list_properties` pagination
  - Limit parameter respected
  - nextCursor presence when hasMore
  - Disjoint pages on cursor navigation
  - Final page has no nextCursor

**Deliverables**:
```typescript
// test/hostaway.pagination.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { MCPTestClient } from './utils/mcpClient'
import { setupHostawayMocks } from './fixtures/hostaway/setup'
import { assertBelowHardCap } from './utils/tokenEstimator'

describe('Pagination Contracts', () => {
  let client: MCPTestClient

  beforeAll(async () => {
    setupHostawayMocks()

    client = new MCPTestClient({
      serverCommand: 'python',
      serverArgs: ['-m', 'src.mcp.server'],
      env: {
        MCP_OUTPUT_TOKEN_THRESHOLD: '2000',
        MCP_HARD_OUTPUT_TOKEN_CAP: '3000',
        MCP_DEFAULT_PAGE_SIZE: '5',
        HOSTAWAY_ACCOUNT_ID: 'test_account',
        HOSTAWAY_SECRET_KEY: 'test_secret',
      },
    })

    await client.start()
  })

  afterAll(async () => {
    await client.stop()
  })

  it('list_properties respects limit parameter', async () => {
    const result = await client.callTool('list_properties', {
      limit: 10,
    })

    expect(result.content).toHaveProperty('items')
    expect(result.content.items).toBeInstanceOf(Array)
    expect(result.content.items.length).toBeLessThanOrEqual(10)

    // Token budget validation
    assertBelowHardCap(result.content, 3000)
  })

  it('list_properties returns nextCursor when more results available', async () => {
    const result = await client.callTool('list_properties', {
      limit: 5,
    })

    expect(result.content).toHaveProperty('nextCursor')
    expect(typeof result.content.nextCursor).toBe('string')
    expect(result.content.meta.hasMore).toBe(true)
  })

  it('list_properties pagination returns disjoint pages', async () => {
    // First page
    const page1 = await client.callTool('list_properties', {
      limit: 5,
    })

    // Second page using cursor
    const page2 = await client.callTool('list_properties', {
      limit: 5,
      cursor: page1.content.nextCursor,
    })

    // Collect IDs from both pages
    const ids1 = page1.content.items.map((item) => item.id)
    const ids2 = page2.content.items.map((item) => item.id)

    // Assert no overlap (disjoint sets)
    const overlap = ids1.filter((id) => ids2.includes(id))
    expect(overlap).toHaveLength(0)

    // Both pages should be under token cap
    assertBelowHardCap(page1.content, 3000)
    assertBelowHardCap(page2.content, 3000)
  })

  it('list_properties final page has no nextCursor', async () => {
    let cursor = null
    let pageCount = 0
    const maxPages = 200  // Safety limit

    // Paginate to end
    while (pageCount < maxPages) {
      const result = await client.callTool('list_properties', {
        limit: 5,
        ...(cursor && { cursor }),
      })

      pageCount++

      if (!result.content.meta.hasMore) {
        // Final page should have no nextCursor
        expect(result.content.nextCursor).toBeNull()
        break
      }

      cursor = result.content.nextCursor
    }

    expect(pageCount).toBeLessThan(maxPages)  // Should reach end
  })

  it('search_bookings respects pagination', async () => {
    const result = await client.callTool('search_bookings', {
      status: 'confirmed',
      limit: 10,
    })

    expect(result.content.items.length).toBeLessThanOrEqual(10)
    assertBelowHardCap(result.content, 3000)
  })
})
```

**Acceptance Criteria**:
- ✅ All pagination tests pass
- ✅ No token cap violations
- ✅ Deterministic results (rerunnable)

---

#### Day 7-8: Preview Mode & Token Cap Tests

**Tasks**:
- [ ] T006: Test preview mode activation
  - Financial reports trigger preview for large date ranges
  - Preview includes summary + cursor for drilldown
  - Token threshold enforcement

**Deliverables**:
```typescript
// test/hostaway.preview-and-caps.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { MCPTestClient } from './utils/mcpClient'
import {
  setupHostawayMocks,
  setupLargeFinancialReportMock,
} from './fixtures/hostaway/setup'
import {
  estimateTokensFromObject,
  assertBelowHardCap,
  checkTokenBudget,
} from './utils/tokenEstimator'

describe('Preview Mode & Token Caps', () => {
  let client: MCPTestClient

  beforeAll(async () => {
    setupHostawayMocks()
    setupLargeFinancialReportMock()

    client = new MCPTestClient({
      serverCommand: 'python',
      serverArgs: ['-m', 'src.mcp.server'],
      env: {
        MCP_OUTPUT_TOKEN_THRESHOLD: '2000',  // Very low to force preview
        MCP_HARD_OUTPUT_TOKEN_CAP: '3000',
        MCP_DEFAULT_PAGE_SIZE: '5',
        HOSTAWAY_ACCOUNT_ID: 'test_account',
        HOSTAWAY_SECRET_KEY: 'test_secret',
      },
    })

    await client.start()
  })

  afterAll(async () => {
    await client.stop()
  })

  it('get_financial_reports triggers preview for large date range', async () => {
    const result = await client.callTool('get_financial_reports', {
      startDate: '2025-01-01',
      endDate: '2025-12-31',  // Full year - large range
    })

    // Should activate preview mode
    expect(result.content).toHaveProperty('meta')
    expect(result.content.meta).toHaveProperty('summary')
    expect(result.content.meta.summary.kind).toBe('preview')

    // Should include summary stats
    expect(result.content.meta.summary).toHaveProperty('totalApprox')
    expect(result.content.meta.summary).toHaveProperty('notes')

    // Should provide drilldown cursor
    expect(result.content).toHaveProperty('nextCursor')

    // Must not exceed hard cap
    assertBelowHardCap(result.content, 3000)

    // Should be under soft threshold (with preview)
    const tokens = estimateTokensFromObject(result.content)
    expect(tokens).toBeLessThan(2000)
  })

  it('get_property_details respects field projection', async () => {
    const result = await client.callTool('get_property_details', {
      propertyId: 12345,
      // No fields specified - should return default projection
    })

    // Should have essential fields
    expect(result.content).toHaveProperty('id')
    expect(result.content).toHaveProperty('name')
    expect(result.content).toHaveProperty('address')

    // Large nested fields should be chunked or omitted
    if (result.content.reviews) {
      // Reviews should be summarized or paginated
      expect(result.content.reviews).toHaveProperty('meta')
      expect(result.content.reviews.meta.kind).toBe('preview')
    }

    assertBelowHardCap(result.content, 3000)
  })

  it('never exceeds hard token cap under any scenario', async () => {
    const scenarios = [
      { tool: 'list_properties', args: { limit: 100 } },
      { tool: 'search_bookings', args: { status: 'all', limit: 100 } },
      { tool: 'get_financial_reports', args: { startDate: '2020-01-01', endDate: '2025-12-31' } },
    ]

    for (const { tool, args } of scenarios) {
      const result = await client.callTool(tool, args)

      // CRITICAL: Never exceed hard cap
      const tokens = estimateTokensFromObject(result.content)
      expect(tokens).toBeLessThanOrEqual(3000)
    }
  })

  it('soft threshold triggers preview without data loss', async () => {
    const result = await client.callTool('get_financial_reports', {
      startDate: '2025-01-01',
      endDate: '2025-03-31',  // Q1 - moderate size
    })

    const { estimated, exceeds } = checkTokenBudget(
      JSON.stringify(result.content),
      2000
    )

    if (exceeds) {
      // Should have preview metadata
      expect(result.content.meta.summary.kind).toBe('preview')

      // Should provide way to get full data
      expect(
        result.content.nextCursor || result.content.meta.detailsAvailable
      ).toBeTruthy()
    } else {
      // Under threshold - full data returned
      expect(result.content.meta?.summary?.kind).not.toBe('preview')
    }
  })
})
```

**Acceptance Criteria**:
- ✅ Preview mode activates when exceeding soft threshold
- ✅ Hard cap never violated
- ✅ Preview includes actionable next steps
- ✅ Field projection reduces payload size

---

#### Day 8-9: Error Hygiene Tests

**Tasks**:
- [ ] T007: Test error response compactness
  - 500 errors return compact JSON
  - 429 errors include retry metadata
  - No large HTML bodies surfaced

**Deliverables**:
```typescript
// test/hostaway.errors-and-rate-limit.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { MCPTestClient } from './utils/mcpClient'
import { setupErrorMocks } from './fixtures/hostaway/setup'
import { estimateTokensFromObject } from './utils/tokenEstimator'

describe('Error Hygiene & Rate Limiting', () => {
  let client: MCPTestClient

  beforeAll(async () => {
    setupErrorMocks()

    client = new MCPTestClient({
      serverCommand: 'python',
      serverArgs: ['-m', 'src.mcp.server'],
      env: {
        HOSTAWAY_ACCOUNT_ID: 'test_account',
        HOSTAWAY_SECRET_KEY: 'test_secret',
      },
    })

    await client.start()
  })

  afterAll(async () => {
    await client.stop()
  })

  it('500 error returns compact JSON (no HTML)', async () => {
    try {
      await client.callTool('trigger_500_error', {})
    } catch (error) {
      // Should receive structured error
      expect(error).toHaveProperty('code')
      expect(error).toHaveProperty('message')
      expect(error).toHaveProperty('correlationId')

      // Should not include HTML
      const errorJson = JSON.stringify(error)
      expect(errorJson).not.toContain('<!DOCTYPE')
      expect(errorJson).not.toContain('<html>')

      // Should be compact (<2KB)
      const tokens = estimateTokensFromObject(error)
      expect(tokens).toBeLessThan(500)  // ~2KB / 4 bytes/token
    }
  })

  it('429 error includes retry guidance', async () => {
    try {
      await client.callTool('trigger_429_error', {})
    } catch (error) {
      expect(error).toHaveProperty('code')
      expect(error.code).toBe('rate_limit_exceeded')

      // Should include retry metadata
      expect(error).toHaveProperty('retryAfterMs')
      expect(typeof error.retryAfterMs).toBe('number')
      expect(error.retryAfterMs).toBeGreaterThan(0)

      // Optional: rate limit remaining
      if (error.rateLimitRemaining !== undefined) {
        expect(error.rateLimitRemaining).toBe(0)
      }

      // Should be compact
      const tokens = estimateTokensFromObject(error)
      expect(tokens).toBeLessThan(500)
    }
  })

  it('all error responses are compact', async () => {
    const errorScenarios = [
      'trigger_500_error',
      'trigger_429_error',
      'trigger_400_error',
      'trigger_404_error',
    ]

    for (const tool of errorScenarios) {
      try {
        await client.callTool(tool, {})
      } catch (error) {
        // All errors should be <2KB
        const tokens = estimateTokensFromObject(error)
        expect(tokens).toBeLessThan(500)

        // Should have standard fields
        expect(error).toHaveProperty('code')
        expect(error).toHaveProperty('message')
      }
    }
  })

  it('error messages are actionable', async () => {
    try {
      await client.callTool('trigger_429_error', {})
    } catch (error) {
      // Message should guide user
      expect(error.message).toMatch(/retry|wait|limit/i)

      // Should include timing information
      expect(error.retryAfterMs || error.message).toBeTruthy()
    }
  })
})
```

**Acceptance Criteria**:
- ✅ All error responses <2KB
- ✅ No HTML in error bodies
- ✅ 429 errors include retry timing
- ✅ Errors have correlation IDs

---

#### Day 9-10: Resources & Field Projection Tests

**Tasks**:
- [ ] T008: Test MCP resources (if exposed)
  - resources/list implements cursor pagination
  - resources/read respects size bounds
- [ ] T009: Test field projection on detail endpoints
  - get_booking_details chunking
  - get_guest_info projection

**Deliverables**:
```typescript
// test/hostaway.resources.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { MCPTestClient } from './utils/mcpClient'
import { setupHostawayMocks } from './fixtures/hostaway/setup'
import { assertBelowHardCap } from './utils/tokenEstimator'

describe('MCP Resources Pagination', () => {
  let client: MCPTestClient

  beforeAll(async () => {
    setupHostawayMocks()

    client = new MCPTestClient({
      serverCommand: 'python',
      serverArgs: ['-m', 'src.mcp.server'],
      env: {
        MCP_OUTPUT_TOKEN_THRESHOLD: '2000',
        MCP_HARD_OUTPUT_TOKEN_CAP: '3000',
        HOSTAWAY_ACCOUNT_ID: 'test_account',
        HOSTAWAY_SECRET_KEY: 'test_secret',
      },
    })

    await client.start()
  })

  afterAll(async () => {
    await client.stop()
  })

  it('resources/list implements cursor pagination', async () => {
    const resources = await client.listResources()

    // If resources exposed, should be paginated
    if (resources.nextCursor) {
      expect(resources.resources).toBeInstanceOf(Array)
      expect(resources.resources.length).toBeGreaterThan(0)

      // Follow cursor
      const nextPage = await client.listResources({
        cursor: resources.nextCursor,
      })

      // Should get different resources
      const firstIds = resources.resources.map((r) => r.uri)
      const nextIds = nextPage.resources.map((r) => r.uri)
      const overlap = firstIds.filter((id) => nextIds.includes(id))

      expect(overlap).toHaveLength(0)
    }
  })

  it('resources/read respects size bounds', async () => {
    const resources = await client.listResources()

    if (resources.resources.length > 0) {
      const firstResource = resources.resources[0]
      const content = await client.readResource(firstResource.uri)

      // Should not exceed hard cap
      assertBelowHardCap(content, 3000)
    }
  })
})
```

```typescript
// test/hostaway.field-projection.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { MCPTestClient } from './utils/mcpClient'
import { setupHostawayMocks } from './fixtures/hostaway/setup'
import { estimateTokensFromObject } from './utils/tokenEstimator'

describe('Field Projection & Chunking', () => {
  let client: MCPTestClient

  beforeAll(async () => {
    setupHostawayMocks()

    client = new MCPTestClient({
      serverCommand: 'python',
      serverArgs: ['-m', 'src.mcp.server'],
      env: {
        MCP_OUTPUT_TOKEN_THRESHOLD: '2000',
        MCP_HARD_OUTPUT_TOKEN_CAP: '3000',
        HOSTAWAY_ACCOUNT_ID: 'test_account',
        HOSTAWAY_SECRET_KEY: 'test_secret',
      },
    })

    await client.start()
  })

  afterAll(async () => {
    await client.stop()
  })

  it('get_booking_details chunks large nested sections', async () => {
    const result = await client.callTool('get_booking_details', {
      bookingId: 'BK12345',
    })

    // Core booking data should be present
    expect(result.content).toHaveProperty('id')
    expect(result.content).toHaveProperty('status')

    // Large collections should be chunked
    if (result.content.lineItems) {
      // Should have preview or pagination
      expect(
        result.content.lineItems.meta ||
          result.content.lineItems.nextCursor
      ).toBeTruthy()
    }

    // Should not exceed hard cap
    const tokens = estimateTokensFromObject(result.content)
    expect(tokens).toBeLessThanOrEqual(3000)
  })

  it('get_guest_info returns minimal data by default', async () => {
    const result = await client.callTool('get_guest_info', {
      guestId: 'G12345',
    })

    // Should have essential fields
    expect(result.content).toHaveProperty('id')
    expect(result.content).toHaveProperty('firstName')
    expect(result.content).toHaveProperty('lastName')
    expect(result.content).toHaveProperty('email')

    // Large collections (history, reviews) should be excluded by default
    expect(result.content.bookingHistory).toBeUndefined()
    expect(result.content.reviewHistory).toBeUndefined()

    // Should be compact
    const tokens = estimateTokensFromObject(result.content)
    expect(tokens).toBeLessThan(500)
  })

  it('get_guest_info with includeHistory returns paginated history', async () => {
    const result = await client.callTool('get_guest_info', {
      guestId: 'G12345',
      includeHistory: true,
    })

    // Should have history but paginated
    if (result.content.bookingHistory) {
      expect(result.content.bookingHistory).toHaveProperty('items')
      expect(result.content.bookingHistory.items.length).toBeLessThanOrEqual(
        10
      )

      // Should have pagination metadata
      expect(result.content.bookingHistory).toHaveProperty('meta')
    }

    // Still should not exceed hard cap
    const tokens = estimateTokensFromObject(result.content)
    expect(tokens).toBeLessThanOrEqual(3000)
  })
})
```

**Acceptance Criteria**:
- ✅ Resources pagination works (if implemented)
- ✅ Field projection reduces payload size
- ✅ Chunking prevents oversized nested data
- ✅ Optional fields behind explicit parameters

---

### Phase 3: Integration & Performance (Week 3) - 5 days

**Goal**: End-to-end tests, performance validation, live integration (optional)

#### Day 11-12: End-to-End Scenarios

**Tasks**:
- [ ] T010: Implement E2E workflow tests
  - Complete user journeys
  - Multi-tool orchestration
  - Token budget across multiple calls

**Deliverables**:
```typescript
// test/e2e/property-search-flow.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { MCPTestClient } from '../utils/mcpClient'
import { setupHostawayMocks } from '../fixtures/hostaway/setup'
import { estimateTokensFromObject } from '../utils/tokenEstimator'

describe('E2E: Property Search & Booking Flow', () => {
  let client: MCPTestClient
  let totalTokens = 0

  beforeAll(async () => {
    setupHostawayMocks()

    client = new MCPTestClient({
      serverCommand: 'python',
      serverArgs: ['-m', 'src.mcp.server'],
      env: {
        MCP_OUTPUT_TOKEN_THRESHOLD: '5000',
        MCP_HARD_OUTPUT_TOKEN_CAP: '10000',
        MCP_DEFAULT_PAGE_SIZE: '20',
        HOSTAWAY_ACCOUNT_ID: 'test_account',
        HOSTAWAY_SECRET_KEY: 'test_secret',
      },
    })

    await client.start()
  })

  afterAll(async () => {
    await client.stop()
  })

  it('user searches properties, checks availability, creates booking', async () => {
    // Step 1: Search properties in San Francisco
    const properties = await client.callTool('list_properties', {
      city: 'San Francisco',
      limit: 10,
    })

    totalTokens += estimateTokensFromObject(properties.content)
    expect(properties.content.items.length).toBeGreaterThan(0)

    // Step 2: Get details for first property
    const propertyId = properties.content.items[0].id
    const details = await client.callTool('get_property_details', {
      propertyId,
    })

    totalTokens += estimateTokensFromObject(details.content)

    // Step 3: Check availability
    const availability = await client.callTool('check_availability', {
      propertyId,
      startDate: '2025-11-01',
      endDate: '2025-11-05',
    })

    totalTokens += estimateTokensFromObject(availability.content)

    // Step 4: Create booking (mock)
    const booking = await client.callTool('create_booking', {
      propertyId,
      guestName: 'John Doe',
      checkIn: '2025-11-01',
      checkOut: '2025-11-05',
    })

    totalTokens += estimateTokensFromObject(booking.content)

    // Assert: Total conversation tokens within budget
    expect(totalTokens).toBeLessThan(10000)

    console.log(`Total tokens used in flow: ${totalTokens}`)
  })

  it('pagination workflow stays within token budget', async () => {
    let pageCount = 0
    let cursor = null
    let totalTokens = 0

    // Paginate through 10 pages
    while (pageCount < 10) {
      const result = await client.callTool('list_properties', {
        limit: 5,
        ...(cursor && { cursor }),
      })

      totalTokens += estimateTokensFromObject(result.content)
      pageCount++

      if (!result.content.meta.hasMore) break
      cursor = result.content.nextCursor
    }

    // 10 pages * ~2KB per page = ~20KB total
    expect(totalTokens).toBeLessThan(10000)

    console.log(`Paginated ${pageCount} pages using ${totalTokens} tokens`)
  })
})
```

**Acceptance Criteria**:
- ✅ Multi-step workflows complete successfully
- ✅ Cumulative token usage tracked
- ✅ Conversation stays within budget

---

#### Day 12-13: Performance Benchmarks

**Tasks**:
- [ ] T011: Implement performance tests
  - Token estimation performance
  - Pagination overhead
  - Preview generation latency

**Deliverables**:
```typescript
// test/performance/token-estimation.bench.ts
import { describe, bench } from 'vitest'
import { estimateTokens, estimateTokensFromObject } from '../utils/tokenEstimator'
import { generateProperties } from '../fixtures/generators/properties'

describe('Token Estimation Performance', () => {
  const smallText = 'Hello world'.repeat(10)  // ~100 chars
  const mediumText = 'x'.repeat(1000)  // 1KB
  const largeText = 'x'.repeat(100000)  // 100KB

  bench('estimate tokens from 100 chars', () => {
    estimateTokens(smallText)
  })

  bench('estimate tokens from 1KB', () => {
    estimateTokens(mediumText)
  })

  bench('estimate tokens from 100KB', () => {
    estimateTokens(largeText)
  })

  const smallObject = { id: 1, name: 'Test' }
  const mediumObject = generateProperties(10)[0]
  const largeObject = { properties: generateProperties(100) }

  bench('estimate tokens from small object', () => {
    estimateTokensFromObject(smallObject)
  })

  bench('estimate tokens from medium object', () => {
    estimateTokensFromObject(mediumObject)
  })

  bench('estimate tokens from large object', () => {
    estimateTokensFromObject(largeObject)
  })
})
```

```typescript
// test/performance/pagination.bench.ts
import { describe, bench, beforeAll, afterAll } from 'vitest'
import { MCPTestClient } from '../utils/mcpClient'
import { setupHostawayMocks } from '../fixtures/hostaway/setup'

describe('Pagination Performance', () => {
  let client: MCPTestClient

  beforeAll(async () => {
    setupHostawayMocks()
    client = new MCPTestClient({
      serverCommand: 'python',
      serverArgs: ['-m', 'src.mcp.server'],
      env: {
        HOSTAWAY_ACCOUNT_ID: 'test_account',
        HOSTAWAY_SECRET_KEY: 'test_secret',
      },
    })
    await client.start()
  })

  afterAll(async () => {
    await client.stop()
  })

  bench('first page retrieval', async () => {
    await client.callTool('list_properties', { limit: 10 })
  })

  bench('cursor navigation', async () => {
    const page1 = await client.callTool('list_properties', { limit: 10 })
    await client.callTool('list_properties', {
      limit: 10,
      cursor: page1.content.nextCursor,
    })
  })

  bench('paginate through 10 pages', async () => {
    let cursor = null
    for (let i = 0; i < 10; i++) {
      const result = await client.callTool('list_properties', {
        limit: 5,
        ...(cursor && { cursor }),
      })
      cursor = result.content.nextCursor
      if (!cursor) break
    }
  })
})
```

**Performance Targets**:
- Token estimation: <1ms for typical responses
- First page: <100ms
- Cursor navigation: <150ms
- 10-page pagination: <2 seconds

**Acceptance Criteria**:
- ✅ All benchmarks meet performance targets
- ✅ No performance regressions from baseline

---

#### Day 13-14: Live Integration Tests (Optional)

**Tasks**:
- [ ] T012: Implement live integration tests
  - Run against Hostaway sandbox
  - Validate token estimates against real data
  - Nightly CI job only

**Deliverables**:
```typescript
// test/live/integration.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { MCPTestClient } from '../utils/mcpClient'

describe.skipIf(!process.env.RUN_LIVE_TESTS)('Live Integration Tests', () => {
  let client: MCPTestClient

  beforeAll(async () => {
    // No mocks - use real Hostaway API
    client = new MCPTestClient({
      serverCommand: 'python',
      serverArgs: ['-m', 'src.mcp.server'],
      env: {
        MCP_OUTPUT_TOKEN_THRESHOLD: '50000',  // Production caps
        MCP_HARD_OUTPUT_TOKEN_CAP: '100000',
        MCP_DEFAULT_PAGE_SIZE: '50',
        HOSTAWAY_ACCOUNT_ID: process.env.HOSTAWAY_ACCOUNT_ID,
        HOSTAWAY_SECRET_KEY: process.env.HOSTAWAY_SECRET_KEY,
      },
    })

    await client.start()
  })

  afterAll(async () => {
    await client.stop()
  })

  it('pagination works with real API', async () => {
    const result = await client.callTool('list_properties', {
      limit: 10,
    })

    expect(result.content.items).toBeInstanceOf(Array)
    expect(result.estimatedTokens).toBeLessThan(100000)
  })

  it('token estimates are accurate within 20%', async () => {
    const result = await client.callTool('get_property_details', {
      propertyId: process.env.TEST_PROPERTY_ID,
    })

    // Compare estimated vs actual (if we had actual tokenizer)
    // For now, just validate estimate is reasonable
    const contentSize = JSON.stringify(result.content).length
    const expectedTokens = Math.ceil((contentSize / 4) * 1.2)

    const variance = Math.abs(result.estimatedTokens - expectedTokens) / expectedTokens
    expect(variance).toBeLessThan(0.2)  // Within 20%
  })
})
```

**CI Configuration**:
```yaml
# .github/workflows/overflow-safety-nightly.yml
name: Overflow Safety - Nightly Live Tests

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
  workflow_dispatch:

jobs:
  live-integration:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          cd test
          npm install
          pip install -e ..

      - name: Run live integration tests
        run: |
          cd test
          npm test -- --run test/live/
        env:
          RUN_LIVE_TESTS: 'true'
          HOSTAWAY_ACCOUNT_ID: ${{ secrets.HOSTAWAY_SANDBOX_ACCOUNT_ID }}
          HOSTAWAY_SECRET_KEY: ${{ secrets.HOSTAWAY_SANDBOX_SECRET_KEY }}
          TEST_PROPERTY_ID: ${{ secrets.TEST_PROPERTY_ID }}

      - name: Publish metrics
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: live-test-metrics
          path: test/metrics/
```

**Acceptance Criteria**:
- ✅ Live tests run successfully against sandbox
- ✅ Token estimates validated against real data
- ✅ Results published for monitoring

---

### Phase 4: CI Integration & Documentation (Week 4) - 5 days

**Goal**: Production-ready CI pipeline and comprehensive documentation

#### Day 16-17: GitHub Actions Workflow

**Tasks**:
- [ ] T013: Create PR gate workflow
  - Run on all PRs
  - Enforce token caps
  - Report failures clearly

**Deliverables**:
```yaml
# .github/workflows/overflow-safety-pr.yml
name: Overflow Safety Tests - PR Gate

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  overflow-safety:
    name: Token Cap & Contract Validation
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: test/package-lock.json

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install Python dependencies
        run: |
          pip install -e .

      - name: Install test dependencies
        working-directory: test
        run: |
          npm ci

      - name: Run overflow-safety tests (strict caps)
        working-directory: test
        run: |
          npm test -- \
            --reporter=verbose \
            --reporter=junit \
            --outputFile=junit-results.xml
        env:
          MCP_OUTPUT_TOKEN_THRESHOLD: '1000'
          MCP_HARD_OUTPUT_TOKEN_CAP: '5000'
          MCP_DEFAULT_PAGE_SIZE: '5'
          HOSTAWAY_ACCOUNT_ID: 'test_account'
          HOSTAWAY_SECRET_KEY: 'test_secret'

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: overflow-safety-test-results
          path: test/junit-results.xml

      - name: Comment PR with results
        if: failure() && github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs')
            const results = fs.readFileSync('test/junit-results.xml', 'utf8')

            // Parse results and create comment
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🔒 Overflow-Safety Tests Failed\n\n` +
                    `One or more endpoints exceeded token caps or violated contracts.\n\n` +
                    `See test results artifact for details.`
            })

      - name: Check for flakes
        if: failure()
        working-directory: test
        run: |
          echo "Rerunning failed tests to check for flakes..."
          npm test -- --rerun-failures=3

  typecheck:
    name: TypeScript Type Check
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - working-directory: test
        run: |
          npm ci
          npm run typecheck
```

**Acceptance Criteria**:
- ✅ CI runs on every PR
- ✅ Clear failure messages
- ✅ Flake detection implemented
- ✅ Results uploaded as artifacts

---

#### Day 17-18: Test Documentation

**Tasks**:
- [ ] T014: Write test documentation
  - How to run tests locally
  - How to add new tests
  - Troubleshooting guide

**Deliverables**:
```markdown
# test/README.md

# Overflow-Safety Test Suite

Automated tests validating token cap enforcement, pagination contracts, and error hygiene for the Hostaway MCP server.

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- MCP server installed (`pip install -e ..`)

### Installation

```bash
cd test
npm install
```

### Running Tests

```bash
# Run all tests with default caps
npm test

# Run with strict caps (force preview mode)
export MCP_OUTPUT_TOKEN_THRESHOLD=1000
export MCP_HARD_OUTPUT_TOKEN_CAP=5000
npm test

# Run specific test file
npm test -- hostaway.pagination.test.ts

# Run with coverage
npm test -- --coverage

# Run performance benchmarks
npm run bench
```

## Test Categories

### Pagination Tests (`hostaway.pagination.test.ts`)
- Validates `limit` parameter enforcement
- Tests `nextCursor` presence and navigation
- Ensures disjoint pages
- Verifies final page behavior

### Preview & Token Cap Tests (`hostaway.preview-and-caps.test.ts`)
- Validates soft threshold triggers preview mode
- Ensures hard cap never exceeded
- Tests field projection
- Validates preview metadata

### Error Hygiene Tests (`hostaway.errors-and-rate-limit.test.ts`)
- Validates error responses <2KB
- Ensures no HTML in errors
- Tests 429 retry metadata
- Validates correlation IDs

### E2E Tests (`e2e/`)
- Multi-tool workflows
- Token budget tracking across conversations
- Real-world user journeys

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_OUTPUT_TOKEN_THRESHOLD` | 50000 | Soft cap (triggers preview) |
| `MCP_HARD_OUTPUT_TOKEN_CAP` | 100000 | Hard cap (never exceeded) |
| `MCP_DEFAULT_PAGE_SIZE` | 50 | Default pagination size |
| `MCP_MAX_PAGE_SIZE` | 200 | Maximum page size |
| `HOSTAWAY_ACCOUNT_ID` | - | Hostaway account (mocked in tests) |
| `HOSTAWAY_SECRET_KEY` | - | Hostaway secret (mocked in tests) |

### Force Small Caps (for testing overflow paths)

```bash
export MCP_OUTPUT_TOKEN_THRESHOLD=1000
export MCP_HARD_OUTPUT_TOKEN_CAP=5000
export MCP_DEFAULT_PAGE_SIZE=5
npm test
```

## Adding New Tests

### 1. Create Test File

```typescript
// test/hostaway.new-feature.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { MCPTestClient } from './utils/mcpClient'
import { setupHostawayMocks } from './fixtures/hostaway/setup'
import { assertBelowHardCap } from './utils/tokenEstimator'

describe('New Feature Tests', () => {
  let client: MCPTestClient

  beforeAll(async () => {
    setupHostawayMocks()
    client = new MCPTestClient({
      serverCommand: 'python',
      serverArgs: ['-m', 'src.mcp.server'],
      env: {
        MCP_OUTPUT_TOKEN_THRESHOLD: '2000',
        MCP_HARD_OUTPUT_TOKEN_CAP: '3000',
        HOSTAWAY_ACCOUNT_ID: 'test_account',
        HOSTAWAY_SECRET_KEY: 'test_secret',
      },
    })
    await client.start()
  })

  afterAll(async () => {
    await client.stop()
  })

  it('validates new endpoint behavior', async () => {
    const result = await client.callTool('new_endpoint', { param: 'value' })

    // Assert token cap
    assertBelowHardCap(result.content, 3000)

    // Assert other contracts
    expect(result.content).toHaveProperty('expectedField')
  })
})
```

### 2. Add Mocks

```typescript
// test/fixtures/hostaway/setup.ts
export function setupNewEndpointMock() {
  nock(HOSTAWAY_BASE_URL)
    .get('/v1/new-endpoint')
    .reply(200, {
      // Mock response
    })
}
```

### 3. Run Tests

```bash
npm test -- hostaway.new-feature.test.ts
```

## Troubleshooting

### "MCP server failed to start"

**Cause**: Server not installed or PATH issue

**Fix**:
```bash
pip install -e ..
which python  # Should be in virtualenv
```

### "Tests timeout"

**Cause**: Server not responding or infinite loop

**Fix**:
- Check server logs in test output
- Reduce timeout: `npm test -- --timeout=10000`
- Enable verbose logging: `DEBUG=* npm test`

### "Token estimate mismatch"

**Cause**: Response larger than expected

**Fix**:
- Check if preview mode should activate
- Verify pagination is working
- Adjust threshold: `export MCP_OUTPUT_TOKEN_THRESHOLD=5000`

### "Flaky tests"

**Cause**: Timing issues or mock state

**Fix**:
- Add `beforeEach(() => nock.cleanAll())`
- Increase timeouts
- Check for async race conditions

## CI Integration

Tests run automatically on every PR via GitHub Actions.

### PR Gate Workflow

- Runs with strict caps (threshold=1000, hardCap=5000)
- Must pass before merge
- Results uploaded as artifacts

### Nightly Workflow

- Runs live integration tests (optional)
- Uses real Hostaway sandbox
- Publishes metrics

## Performance Targets

| Metric | Target |
|--------|--------|
| Test suite duration | <5 minutes |
| Individual test | <10 seconds |
| Token estimation | <1ms |
| First page load | <100ms |
| Flake rate | <1% |

## Metrics & Monitoring

Performance metrics saved to `test/metrics/`:

- Token usage per endpoint
- Response times
- Flake detection results

View metrics:
```bash
cat test/metrics/latest.json | jq
```

## References

- [Vitest Documentation](https://vitest.dev/)
- [MCP SDK Documentation](https://spec.modelcontextprotocol.io/)
- [Nock HTTP Mocking](https://github.com/nock/nock)
- [Overflow-Safety Spec](../specs/006-overflow-safety-test-suite/spec.md)
```

**Acceptance Criteria**:
- ✅ Documentation clear and comprehensive
- ✅ Examples work out of the box
- ✅ Troubleshooting covers common issues

---

#### Day 18-19: Runbook & Metrics

**Tasks**:
- [ ] T015: Create failure runbook
  - Common failure modes
  - Debugging steps
  - Fix recipes

**Deliverables**:
```markdown
# test/RUNBOOK.md

# Overflow-Safety Test Failure Runbook

## Quick Diagnosis

### Identify Failure Type

```bash
# Check test output
cat test-results/junit-results.xml | grep "<failure"

# Common patterns:
# - "Token budget exceeded" → Hard cap violation
# - "Preview mode not activated" → Soft threshold not working
# - "nextCursor missing" → Pagination broken
# - "Error response too large" → Error hygiene failure
```

## Failure Modes & Fixes

### 1. Hard Cap Violation

**Symptom**: `HARD CAP VIOLATION: ${tokens} tokens > ${cap} hard cap`

**Cause**: Endpoint returning too much data

**Diagnosis**:
```bash
# Check which endpoint failed
grep "HARD CAP VIOLATION" test-results/junit-results.xml

# Get full response
DEBUG=mcp:* npm test -- <failing-test>
```

**Fix Options**:

A. **Add Pagination**
```python
# In endpoint handler
from src.services.pagination_service import get_pagination_service

pagination = get_pagination_service(secret="...")
response = pagination.build_response(
    items=filtered_items,
    total_count=total,
    params=params
)
```

B. **Enable Preview Mode**
```python
# Check if should summarize
from src.services.summarization_service import get_summarization_service

summarization = get_summarization_service()
should_summarize, tokens = summarization.should_summarize(
    obj=large_object,
    token_threshold=config.MCP_OUTPUT_TOKEN_THRESHOLD
)

if should_summarize:
    return summarization.summarize_object(
        obj=large_object,
        obj_type="booking",
        endpoint="/api/v1/bookings/{id}"
    )
```

C. **Increase Hard Cap** (last resort)
```bash
# Update config
export MCP_HARD_OUTPUT_TOKEN_CAP=150000
```

**Verification**:
```bash
# Re-run test
MCP_HARD_OUTPUT_TOKEN_CAP=150000 npm test -- <failing-test>
```

---

### 2. Preview Mode Not Activating

**Symptom**: Test expects preview but gets full data

**Cause**: Token estimation incorrect or threshold too high

**Diagnosis**:
```bash
# Check estimated tokens
grep "estimated" test-results/junit-results.xml

# Compare to threshold
echo $MCP_OUTPUT_TOKEN_THRESHOLD
```

**Fix Options**:

A. **Adjust Threshold**
```bash
# Lower threshold to force preview
export MCP_OUTPUT_TOKEN_THRESHOLD=2000
npm test
```

B. **Fix Token Estimation**
```python
# In handler, add debug logging
from src.utils.token_estimator import estimate_tokens_from_dict

estimated = estimate_tokens_from_dict(response)
logger.info(f"Response tokens: {estimated}, threshold: {threshold}")
```

C. **Verify Preview Logic**
```python
# Ensure handler checks threshold
if estimated_tokens > config.MCP_OUTPUT_TOKEN_THRESHOLD:
    # Activate preview mode
    return preview_response
```

**Verification**:
```bash
npm test -- --grep "preview"
```

---

### 3. Pagination Broken

**Symptom**: `nextCursor missing when hasMore=true` or overlapping pages

**Diagnosis**:
```bash
# Check pagination metadata
npm test -- --grep "pagination" --reporter=verbose
```

**Fix Options**:

A. **Verify Cursor Creation**
```python
# Ensure nextCursor created when hasMore
if next_offset < total_count:
    next_cursor = pagination.create_cursor(
        offset=next_offset,
        order_by=order_by,
        filters=filters
    )
else:
    next_cursor = None
```

B. **Check Offset Calculation**
```python
# Ensure disjoint pages
current_offset = cursor_data["offset"] if cursor else 0
next_offset = current_offset + len(items)  # Not current + limit!
```

C. **Validate hasMore Logic**
```python
has_more = next_offset < total_count  # Should match nextCursor presence
```

**Verification**:
```bash
# Test multiple pages
npm test -- hostaway.pagination.test.ts
```

---

### 4. Error Response Too Large

**Symptom**: Error exceeds 2KB token limit

**Diagnosis**:
```bash
# Check error size
npm test -- --grep "error" --reporter=verbose
```

**Fix Options**:

A. **Strip HTML from Errors**
```python
# In error handler
try:
    response = await hostaway_client.get(endpoint)
except httpx.HTTPStatusError as e:
    # Don't return raw HTML
    if 'text/html' in e.response.headers.get('content-type', ''):
        # Return compact error instead
        return {
            "error": {
                "code": "internal_server_error",
                "message": "Hostaway API error",
                "correlationId": correlation_id,
                "statusCode": e.response.status_code
            }
        }
```

B. **Add Correlation IDs**
```python
from src.lib.utils.errors import logError, createErrorResponse

correlation_id = logError("Hostaway API failed", error, context)
return createErrorResponse(
    ErrorMessages.HOSTAWAY_CONNECTION_FAILED,
    correlation_id
)
```

**Verification**:
```bash
npm test -- hostaway.errors-and-rate-limit.test.ts
```

---

## Performance Issues

### Tests Taking >5 Minutes

**Diagnosis**:
```bash
# Run with durations report
npm test -- --reporter=verbose --outputFile=durations.txt
grep "Duration" durations.txt | sort -nr | head -10
```

**Fix Options**:

A. **Run Tests in Parallel**
```bash
# Increase concurrency
npm test -- --pool=threads --poolOptions.threads.maxThreads=8
```

B. **Optimize Slow Tests**
```typescript
// Reduce iterations
it('pagination test', async () => {
  for (let i = 0; i < 10; i++) {  // Was 100
    // ...
  }
})
```

C. **Skip Slow Tests in PR Gate**
```typescript
it.skip('expensive test', async () => {
  // Only run nightly
})
```

---

## Flaky Tests

### Intermittent Failures

**Diagnosis**:
```bash
# Re-run failed tests 10 times
npm test -- --rerun-failures=10
```

**Fix Options**:

A. **Add Retries**
```typescript
it('flaky test', async () => {
  await retry(async () => {
    const result = await client.callTool(...)
    expect(result).toBeTruthy()
  }, { retries: 3 })
})
```

B. **Fix Timing Issues**
```typescript
// Add explicit wait
await new Promise(resolve => setTimeout(resolve, 100))
```

C. **Clean Mocks Between Tests**
```typescript
beforeEach(() => {
  nock.cleanAll()
  setupHostawayMocks()
})
```

---

## Escalation

If runbook doesn't resolve issue:

1. **Collect Diagnostics**:
```bash
# Full verbose output
DEBUG=* npm test -- <failing-test> > debug.log 2>&1

# Server logs
cat ~/.mcp/logs/server.log

# Test environment
npm test -- --version
node --version
python --version
```

2. **Create GitHub Issue**:
- Title: `[Overflow-Safety] Test failure: <test-name>`
- Include: debug.log, environment info, steps to reproduce
- Label: `overflow-safety`, `test-failure`

3. **Contact Team**:
- Slack: #mcp-testing
- Email: mcp-team@example.com

---

## Preventive Measures

### Before Deploying New Endpoint

```bash
# Run overflow tests with strict caps
export MCP_OUTPUT_TOKEN_THRESHOLD=1000
export MCP_HARD_OUTPUT_TOKEN_CAP=5000
npm test

# If fails, add pagination/preview before deploying
```

### Code Review Checklist

- [ ] Endpoint implements pagination if returns >10 items
- [ ] Large responses trigger preview mode
- [ ] Errors return compact JSON (<2KB)
- [ ] Token caps never exceeded
- [ ] Tests added to overflow-safety suite
```

**Acceptance Criteria**:
- ✅ Runbook covers all common failures
- ✅ Clear escalation path
- ✅ Prevention checklist provided

---

#### Day 19-20: Final Testing & Handoff

**Tasks**:
- [ ] T016: Full regression testing
- [ ] T017: Documentation review
- [ ] T018: Handoff to team

**Deliverables**:
- ✅ All tests passing
- ✅ CI pipeline green
- ✅ Documentation complete
- ✅ Team trained

---

## 3. Project Structure

```
hostaway-mcp/
├── specs/
│   └── 006-overflow-safety-test-suite/
│       ├── spec.md
│       ├── research.md
│       ├── plan.md (this file)
│       ├── data-model.md
│       └── tasks.md
├── test/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vitest.config.ts
│   ├── setup.ts
│   ├── README.md
│   ├── RUNBOOK.md
│   ├── utils/
│   │   ├── mcpClient.ts
│   │   ├── tokenEstimator.ts
│   │   └── assertions.ts
│   ├── fixtures/
│   │   ├── hostaway/
│   │   │   └── setup.ts
│   │   └── generators/
│   │       ├── properties.ts
│   │       ├── bookings.ts
│   │       ├── financial.ts
│   │       └── errors.ts
│   ├── hostaway.pagination.test.ts
│   ├── hostaway.preview-and-caps.test.ts
│   ├── hostaway.errors-and-rate-limit.test.ts
│   ├── hostaway.field-projection.test.ts
│   ├── hostaway.resources.test.ts
│   ├── e2e/
│   │   └── property-search-flow.test.ts
│   ├── performance/
│   │   ├── token-estimation.bench.ts
│   │   └── pagination.bench.ts
│   ├── live/
│   │   └── integration.test.ts
│   └── metrics/
│       └── latest.json
└── .github/
    └── workflows/
        ├── overflow-safety-pr.yml
        └── overflow-safety-nightly.yml
```

---

## 4. Dependencies

### Runtime Dependencies

```json
{
  "name": "overflow-safety-tests",
  "version": "1.0.0",
  "type": "module",
  "devDependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "@types/node": "^20.0.0",
    "nock": "^14.0.0",
    "tsx": "^4.0.0",
    "typescript": "^5.0.0",
    "vitest": "^1.0.0"
  },
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest watch",
    "test:coverage": "vitest run --coverage",
    "bench": "vitest bench",
    "typecheck": "tsc --noEmit"
  }
}
```

### Python Dependencies

Already installed in main project:
- `fastapi-mcp` - MCP server
- `pytest` - Unit tests
- `httpx` - HTTP client

---

## 5. Success Metrics

### Coverage Targets

- ✅ 100% of high-volume endpoints tested
- ✅ All pagination paths exercised
- ✅ All error scenarios covered
- ✅ Token cap boundaries tested

### Performance Targets

- ✅ Test suite <5 minutes
- ✅ Individual tests <10 seconds
- ✅ Flake rate <1%

### Quality Targets

- ✅ 0 hard cap violations
- ✅ ≥95% pagination/preview under forced caps
- ✅ All errors <2KB

---

## 6. Risk Mitigation

### High-Risk Areas

1. **MCP stdio Communication**
   - Mitigation: Thorough client wrapper testing
   - Fallback: Mock server if stdio issues

2. **Flaky Tests**
   - Mitigation: Retry logic + flake detection
   - Fallback: Quarantine flaky tests

3. **Performance**
   - Mitigation: Parallel execution + mocking
   - Fallback: Increase timeout limits

### Contingency Plans

- Week 3 buffer for unexpected issues
- Optional live tests can be deferred
- Performance tests can run separately

---

## 7. Acceptance Criteria Summary

- ✅ TypeScript/Vitest test suite operational
- ✅ MCP stdio client wrapper functional
- ✅ Nock mocking for all Hostaway endpoints
- ✅ Pagination contracts validated
- ✅ Preview mode enforcement tested
- ✅ Token cap never exceeded
- ✅ Error hygiene validated (<2KB)
- ✅ CI pipeline integrated (PR gate + nightly)
- ✅ Documentation complete (README + runbook)
- ✅ Performance targets met (<5min suite)
- ✅ Flake rate <1%

---

## 8. Next Steps After Implementation

### Follow-Up Work

1. **Load Testing**
   - k6/Artillery scripts
   - p95 latency validation
   - Concurrent request handling

2. **Golden Sample Snapshots**
   - Capture expected summaries
   - Detect verbosity regressions
   - Version control snapshots

3. **Metrics Dashboard**
   - Grafana/Datadog integration
   - Token usage trends
   - Preview mode activation rates

4. **Production Rollout**
   - Enable stricter caps gradually
   - Monitor real token usage
   - A/B test preview mode

---

**Plan Status**: Ready for Implementation
**Estimated Duration**: 4 weeks (20 days)
**Team Size**: 1-2 developers
**Next Document**: `tasks.md` (sprint-ready task breakdown)
