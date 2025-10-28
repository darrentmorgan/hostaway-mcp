/**
 * Token estimation utility for Claude context window management
 *
 * Character-based estimation with 20% safety margin.
 * Based on research.md R001: 1 token ≈ 4 characters heuristic.
 */

import { expect } from 'vitest';

/**
 * Estimate Claude token count from text
 *
 * Uses 4 characters per token heuristic with 20% safety margin.
 * Target performance: <1ms for typical API responses.
 *
 * @param text - Text to estimate tokens for
 * @returns Estimated token count (includes 20% safety margin)
 *
 * @example
 * ```ts
 * estimateTokens("Hello world") // Returns 4
 * estimateTokens("A".repeat(1000)) // Returns 300
 * ```
 */
export function estimateTokens(text: string): number {
  const charCount = text.length;
  const baseEstimate = charCount / 4;
  const safetyMargin = baseEstimate * 0.20;
  return Math.ceil(baseEstimate + safetyMargin);
}

/**
 * Estimate tokens from a JavaScript object
 *
 * Serializes object to JSON and estimates tokens from the string representation.
 *
 * @param obj - Object to estimate tokens for
 * @returns Estimated token count
 *
 * @example
 * ```ts
 * estimateTokensFromObject({ id: "BK12345", status: "confirmed" }) // Returns ~12
 * ```
 */
export function estimateTokensFromObject(obj: unknown): number {
  const jsonStr = JSON.stringify(obj);
  return estimateTokens(jsonStr);
}

/**
 * Estimate tokens from an array of items
 *
 * @param items - Array of items to estimate tokens for
 * @returns Estimated token count for entire array
 *
 * @example
 * ```ts
 * estimateTokensFromList([{ id: "1" }, { id: "2" }]) // Returns ~7
 * ```
 */
export function estimateTokensFromList(items: unknown[]): number {
  const jsonStr = JSON.stringify(items);
  return estimateTokens(jsonStr);
}

export interface TokenBudgetResult {
  /** Estimated token count */
  estimated: number;
  /** Whether the threshold was exceeded */
  exceeds: boolean;
  /** Ratio of budget used (1.0 = 100%) */
  ratio: number;
}

/**
 * Check if text exceeds token budget threshold
 *
 * @param text - Text to check
 * @param threshold - Token budget threshold (default: 4000)
 * @returns Token budget analysis
 *
 * @example
 * ```ts
 * checkTokenBudget("Hello".repeat(1000), 4000)
 * // Returns { estimated: 1800, exceeds: false, ratio: 0.45 }
 * ```
 */
export function checkTokenBudget(
  text: string,
  threshold: number = 4000
): TokenBudgetResult {
  const estimated = estimateTokens(text);
  const exceeds = estimated > threshold;
  const ratio = threshold > 0 ? estimated / threshold : 0;

  return { estimated, exceeds, ratio };
}

/**
 * Calculate token reduction needed to meet threshold
 *
 * @param currentTokens - Current estimated token count
 * @param targetThreshold - Target token threshold
 * @returns Reduction analysis
 *
 * @example
 * ```ts
 * estimateReductionNeeded(6000, 4000)
 * // Returns { tokensToReduce: 2000, reductionRatio: 0.33 }
 * ```
 */
export function estimateReductionNeeded(
  currentTokens: number,
  targetThreshold: number = 4000
): { tokensToReduce: number; reductionRatio: number } {
  if (currentTokens <= targetThreshold) {
    return { tokensToReduce: 0, reductionRatio: 0 };
  }

  const tokensToReduce = currentTokens - targetThreshold;
  const reductionRatio = tokensToReduce / currentTokens;

  return { tokensToReduce, reductionRatio };
}

/**
 * Calculate safe page size given average item token count
 *
 * @param avgItemTokens - Average tokens per item in list
 * @param targetThreshold - Target token threshold
 * @param overheadTokens - Overhead tokens for metadata/envelope (default: 200)
 * @returns Recommended page size (minimum 1)
 *
 * @example
 * ```ts
 * calculateSafePageSize(50, 4000) // Returns 76
 * calculateSafePageSize(500, 4000) // Returns 7
 * ```
 */
export function calculateSafePageSize(
  avgItemTokens: number,
  targetThreshold: number = 4000,
  overheadTokens: number = 200
): number {
  const availableTokens = targetThreshold - overheadTokens;
  if (availableTokens <= 0) {
    return 1;
  }

  const pageSize = Math.floor(availableTokens / avgItemTokens);
  return Math.max(1, pageSize);
}

// ============================================================================
// Vitest Assertion Helpers
// ============================================================================

/**
 * Assert that content is within token budget threshold
 *
 * @param content - Content to check (string or object)
 * @param threshold - Token budget threshold
 * @param message - Optional custom error message
 *
 * @example
 * ```ts
 * const response = await mcpClient.callTool("list_properties");
 * assertWithinTokenBudget(response.content, 50000);
 * ```
 */
export function assertWithinTokenBudget(
  content: string | unknown,
  threshold: number,
  message?: string
): void {
  const text = typeof content === 'string' ? content : JSON.stringify(content);
  const result = checkTokenBudget(text, threshold);

  expect(
    result.exceeds,
    message || `Token count ${result.estimated} exceeds threshold ${threshold} (${(result.ratio * 100).toFixed(1)}% of budget)`
  ).toBe(false);
}

/**
 * Assert that content is below hard token cap
 *
 * Hard cap violations are CRITICAL - they indicate a bug in overflow safety.
 *
 * @param content - Content to check (string or object)
 * @param hardCap - Hard cap limit (default: from env or 100000)
 * @param message - Optional custom error message
 *
 * @example
 * ```ts
 * const response = await mcpClient.callTool("get_financial_reports");
 * assertBelowHardCap(response.content); // Uses env MCP_OUTPUT_TOKEN_HARD_CAP
 * ```
 */
export function assertBelowHardCap(
  content: string | unknown,
  hardCap?: number,
  message?: string
): void {
  const cap = hardCap || parseInt(process.env.MCP_OUTPUT_TOKEN_HARD_CAP || '100000', 10);
  const text = typeof content === 'string' ? content : JSON.stringify(content);
  const estimated = estimateTokens(text);

  expect(
    estimated,
    message || `HARD CAP VIOLATION: ${estimated} tokens exceeds hard cap ${cap}`
  ).toBeLessThanOrEqual(cap);
}

/**
 * Assert that preview mode was triggered (for large responses)
 *
 * @param response - Response object to check
 * @param message - Optional custom error message
 *
 * @example
 * ```ts
 * const response = await mcpClient.callTool("get_financial_reports", {
 *   start_date: "2020-01-01",
 *   end_date: "2024-12-31"
 * });
 * assertPreviewMode(response.content);
 * ```
 */
export function assertPreviewMode(
  response: unknown,
  message?: string
): void {
  const obj = typeof response === 'string' ? JSON.parse(response) : response;
  const meta = (obj as { meta?: { summary?: { kind?: string } } }).meta;

  expect(
    meta?.summary?.kind,
    message || 'Expected preview mode to be triggered (meta.summary.kind should be "preview")'
  ).toBe('preview');
}

/**
 * Assert that pagination cursor is present when expected
 *
 * @param response - Response object to check
 * @param shouldHaveCursor - Whether cursor should be present
 * @param message - Optional custom error message
 *
 * @example
 * ```ts
 * const response = await mcpClient.callTool("list_properties", { limit: 10 });
 * if (response.content.hasMore) {
 *   assertPaginationCursor(response.content, true);
 * }
 * ```
 */
export function assertPaginationCursor(
  response: unknown,
  shouldHaveCursor: boolean,
  message?: string
): void {
  const obj = typeof response === 'string' ? JSON.parse(response) : response;
  const cursor = (obj as { nextCursor?: string }).nextCursor;

  if (shouldHaveCursor) {
    expect(
      cursor,
      message || 'Expected pagination cursor to be present'
    ).toBeDefined();
    expect(
      cursor,
      message || 'Expected pagination cursor to be non-empty'
    ).not.toBe('');
  } else {
    // Accept both null (from JSON) and undefined (from JavaScript)
    expect(
      cursor,
      message || 'Expected no pagination cursor (last page)'
    ).toBeFalsy(); // null, undefined, empty string all pass
  }
}
