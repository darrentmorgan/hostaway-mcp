# hostaway-mcp Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-12

## Active Technologies
- Python 3.12+ + FastAPI 0.100+, fastapi-mcp 0.4+, httpx 0.27+, Pydantic 2.0+ (001-we-need-to)
- Python 3.12 (existing v1.0 stack) + FastAPI 0.100+, fastapi-mcp 0.4+, httpx 0.27+ (async), Pydantic 2.0+, pydantic-settings (002-enhance-the-hostaway)
- N/A (stateless, all data retrieved on-demand from Hostaway API) (002-enhance-the-hostaway)
- Python 3.12 (existing backend), TypeScript/JavaScript (Next.js 14 dashboard) (003-we-need-to)
- Supabase PostgreSQL (multi-tenant with RLS), Supabase Vault for credential encryption (003-we-need-to)
- TypeScript 5.x with Next.js 15.5.4, React 19.1.0 + Next.js App Router, shadcn/ui, Tailwind CSS 3.x, Radix UI primitives, Supabase client (browser + server) (004-we-need-to)
- Supabase PostgreSQL (existing schema - no changes needed) (004-we-need-to)
- Python 3.12+ + FastAPI 0.100+, fastapi-mcp 0.4+, httpx 0.27+, Pydantic 2.0+, pydantic-settings (005-project-brownfield-hardening)
- Supabase PostgreSQL (multi-tenant with RLS), Redis/in-memory for pagination cursor cache (005-project-brownfield-hardening)

## Project Structure
```
src/
tests/
```

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Python 3.12+: Follow standard conventions

## Recent Changes
- 005-project-brownfield-hardening: Added Python 3.12+ + FastAPI 0.100+, fastapi-mcp 0.4+, httpx 0.27+, Pydantic 2.0+, pydantic-settings
- 004-we-need-to: Added TypeScript 5.x with Next.js 15.5.4, React 19.1.0 + Next.js App Router, shadcn/ui, Tailwind CSS 3.x, Radix UI primitives, Supabase client (browser + server)
- 003-we-need-to: Added Python 3.12 (existing backend), TypeScript/JavaScript (Next.js 14 dashboard)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
