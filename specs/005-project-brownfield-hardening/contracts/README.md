# API Contracts: MCP Server Context Window Protection

This directory contains OpenAPI 3.0 schema definitions for enhanced response envelopes. All schemas are **additive** (backwards compatible).

## Files

- `pagination.yaml` - Paginated response envelope and pagination parameters
- `token-budget.yaml` - Token budget metadata schemas
- `summarization.yaml` - Summary response envelope schemas

## Usage

These schemas are referenced in the main OpenAPI spec for endpoints that support pagination/summarization. Clients can opt-in by providing `cursor` and `limit` parameters.

## Backwards Compatibility

All new fields are **optional** from the client perspective:
- Clients not using pagination receive first page by default
- Clients not checking `nextCursor` receive partial results (acceptable degradation)
- All existing response fields remain unchanged
