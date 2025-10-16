# Implementation Plan: Production-Ready Dashboard with Design System

**Branch**: `004-we-need-to` | **Date**: 2025-10-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-we-need-to/spec.md`

## Summary

Implement a production-ready dashboard UI with shadcn/ui component library and Tailwind CSS to provide a polished, consistent user interface. Fix the broken usage page to display API metrics, listing counts, and billing projections. Create a reusable component library to accelerate future development while maintaining visual consistency and accessibility standards (WCAG 2.1 Level AA).

**Primary Requirement**: Production-ready dashboard with working usage page and design system
**Technical Approach**: Install and configure shadcn/ui + Tailwind CSS, fix usage page data fetching/rendering, build reusable component library

## Technical Context

**Language/Version**: TypeScript 5.x with Next.js 15.5.4, React 19.1.0
**Primary Dependencies**: Next.js App Router, shadcn/ui, Tailwind CSS 3.x, Radix UI primitives, Supabase client (browser + server)
**Storage**: Supabase PostgreSQL (existing schema - no changes needed)
**Testing**: Playwright (E2E), Jest + React Testing Library (component tests)
**Target Platform**: Modern browsers (Chrome/Firefox/Safari/Edge latest 2 versions), responsive design (320px-2560px)
**Project Type**: Web application (Next.js dashboard - frontend only, no backend changes)
**Performance Goals**: <2s page load, <100ms interaction feedback, Lighthouse score >90
**Constraints**: Must work with Next.js 15 + React 19, no breaking changes to existing routes, maintain backward compatibility
**Scale/Scope**: 5 dashboard pages (Home, Usage, Billing, API Keys, Settings), ~15-20 reusable components, mobile-responsive

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: This is a **frontend-only feature** that does not introduce new API endpoints or MCP tools. The constitution primarily governs backend/API development. However, we apply relevant principles where applicable:

### Applicable Principles

✅ **II. Type Safety (NON-NEGOTIABLE)** - COMPLIANT
- Dashboard uses TypeScript with strict mode
- Supabase database types generated for type-safe queries
- Component props fully typed with TypeScript interfaces
- No `any` types permitted

✅ **IV. Test-Driven Development** - COMPLIANT
- Component tests with React Testing Library
- E2E tests with Playwright for critical flows
- Target: >80% coverage for new components (not existing dashboard pages)

⚠️ **V. Async Performance** - PARTIALLY APPLICABLE
- Dashboard uses Next.js Server Components (async by default)
- Client-side data fetching via Supabase client (async)
- No blocking operations in UI

### Not Applicable (Backend-Focused)

- **I. API-First Design**: No new FastAPI endpoints (dashboard consumes existing APIs)
- **III. Security by Default**: Frontend follows existing auth patterns (no new security layer)

### Constitution Compliance Summary

**Status**: ✅ **COMPLIANT WITH EXCEPTIONS**

This feature is frontend-only and does not introduce new API endpoints, MCP tools, or backend services. The constitution primarily governs backend development. We apply relevant principles (type safety, testing, async patterns) where applicable to frontend code.

**Justification for Non-Applicability**:
- No FastAPI endpoints → API-First Design not applicable
- No new auth mechanisms → Security by Default covered by existing Supabase Auth
- Frontend-only → Backend-specific principles (FastAPI, MCP) not applicable

## Project Structure

### Documentation (this feature)

```
specs/004-we-need-to/
├── plan.md              # This file
├── research.md          # shadcn/ui setup, Tailwind config, Next.js 15 compatibility
├── data-model.md        # UI component models (props, states, design tokens)
├── quickstart.md        # Setup guide for shadcn/ui + Tailwind
├── contracts/           # Component API contracts (not REST APIs)
└── tasks.md             # Implementation tasks (via /speckit.tasks)
```

### Source Code (repository root)

```
dashboard/                         # Next.js 15 App Router (existing)
├── app/
│   ├── (auth)/                   # Authentication pages (existing)
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/              # Dashboard pages (existing - will be updated)
│   │   ├── layout.tsx           # Dashboard layout with navigation
│   │   ├── page.tsx             # Home/overview page
│   │   ├── usage/               # BROKEN - Priority fix
│   │   │   └── page.tsx
│   │   ├── billing/             # Billing & subscription page
│   │   │   └── page.tsx
│   │   ├── api-keys/            # API key management
│   │   │   └── page.tsx
│   │   └── settings/            # Account settings
│   │       └── page.tsx
│   ├── globals.css              # Tailwind directives (existing)
│   └── layout.tsx               # Root layout
│
├── components/                   # NEW - shadcn/ui component library
│   ├── ui/                      # shadcn/ui base components (NEW)
│   │   ├── button.tsx           # Button component
│   │   ├── card.tsx             # Card component
│   │   ├── input.tsx            # Input component
│   │   ├── table.tsx            # Table component
│   │   ├── dialog.tsx           # Modal dialog component
│   │   ├── select.tsx           # Select dropdown
│   │   ├── badge.tsx            # Badge/chip component
│   │   └── skeleton.tsx         # Loading skeleton
│   │
│   ├── usage/                   # Usage page components (existing - will be updated)
│   │   ├── MetricsSummary.tsx  # Metrics cards
│   │   └── UsageChart.tsx      # Chart component
│   │
│   ├── billing/                 # Billing page components (existing)
│   │   ├── SubscriptionCard.tsx
│   │   └── InvoiceHistory.tsx
│   │
│   ├── api-keys/                # API key components (existing)
│   │   ├── APIKeyList.tsx
│   │   └── APIKeyGenerateModal.tsx
│   │
│   └── settings/                # Settings components (existing)
│       └── HostawayCredentials.tsx
│
├── lib/
│   ├── utils.ts                 # NEW - shadcn/ui utility functions (cn helper)
│   ├── supabase/                # Supabase clients (existing)
│   │   ├── client.ts            # Browser client
│   │   ├── server.ts            # Server Component client
│   │   └── middleware.ts        # Auth middleware
│   └── types/
│       └── database.ts          # Generated Supabase types (existing)
│
├── __tests__/                   # NEW - Component tests
│   ├── components/
│   │   └── ui/                 # Tests for shadcn/ui components
│   └── e2e/                    # Playwright E2E tests
│       └── dashboard.spec.ts
│
├── public/                      # Static assets (existing)
├── tailwind.config.ts           # Tailwind configuration (will be updated)
├── components.json              # NEW - shadcn/ui configuration
├── tsconfig.json                # TypeScript config (existing)
├── next.config.js               # Next.js config (existing)
└── package.json                 # Dependencies (will be updated)
```

**Structure Decision**: Web application (Next.js App Router) - frontend only. No backend changes required. Dashboard pages already exist but lack design system and have rendering issues (usage page). We will install shadcn/ui, configure Tailwind properly, fix the usage page, and create a component library.

## Complexity Tracking

*No constitution violations - feature is frontend-only and does not introduce backend complexity*

## Phase 0: Research & Technology Decisions

### Research Tasks

1. **shadcn/ui Setup with Next.js 15 + React 19**
   - **Question**: Is shadcn/ui compatible with Next.js 15 and React 19 (both bleeding edge)?
   - **Research**: Check shadcn/ui docs, GitHub issues, community reports
   - **Deliverable**: Compatibility assessment, potential workarounds or downgrade requirements

2. **Tailwind CSS Configuration for App Router**
   - **Question**: What Tailwind configuration is needed for Next.js App Router with Server Components?
   - **Research**: Next.js + Tailwind docs, App Router best practices
   - **Deliverable**: Tailwind config template, CSS layer setup

3. **Usage Page Bug Diagnosis**
   - **Question**: Why is the usage page broken? Is it data fetching, rendering, or component error?
   - **Research**: Check browser console, network tab, component tree, Supabase query logs
   - **Deliverable**: Root cause analysis, fix strategy

4. **Component Library Architecture**
   - **Question**: How should we organize components (atomic design, feature-based, shadcn/ui pattern)?
   - **Research**: shadcn/ui conventions, Next.js best practices, industry patterns
   - **Deliverable**: Component organization strategy, naming conventions

5. **Accessibility Testing Strategy**
   - **Question**: How do we test and enforce WCAG 2.1 Level AA compliance?
   - **Research**: axe-core, Lighthouse CI, manual testing checklist
   - **Deliverable**: Accessibility testing workflow, automated checks in CI/CD

6. **Chart Library Selection for Usage Page**
   - **Question**: Which charting library works best with shadcn/ui (Recharts, Chart.js, Victory)?
   - **Research**: Compare bundle size, TypeScript support, customizability, accessibility
   - **Deliverable**: Chart library recommendation with rationale

### Technology Decisions

**Note**: Decisions are based on user input and industry best practices. Research will validate or adjust these choices.

| Decision | Choice | Rationale | To Be Validated |
|----------|--------|-----------|-----------------|
| Component Library | shadcn/ui | User requested, industry standard for Next.js, copy-paste approach (full ownership) | Compatibility with Next.js 15 + React 19 |
| CSS Framework | Tailwind CSS 3.x | User requested, works seamlessly with shadcn/ui, utility-first approach | Configuration for App Router |
| UI Primitives | Radix UI | Foundation of shadcn/ui, accessible by default, headless components | None (stable choice) |
| Chart Library | Recharts | React-native charts, good TypeScript support, composable API | Integration with shadcn/ui theme |
| Icon Library | Lucide React | shadcn/ui default, tree-shakeable, consistent style | None (included with shadcn/ui) |
| Form Validation | React Hook Form + Zod | Type-safe validation, excellent DX, integrates with shadcn/ui | None (standard pattern) |
| Testing (Component) | Jest + RTL | Standard React testing, fast unit tests | Setup with Next.js 15 |
| Testing (E2E) | Playwright | Modern, fast, great developer experience, supports Next.js | None (already used in project) |

### Research Deliverable

All findings will be documented in `research.md` with:
- **Decision**: Final choice made
- **Rationale**: Why this choice
- **Alternatives Considered**: What else was evaluated
- **Implementation Notes**: Specific setup steps, gotchas, configuration

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

**Note**: This is a UI-focused feature, so "data model" refers to **component models** (props, state, design tokens), not database schema.

#### UI Component Models

1. **Button**
   - **Props**: `variant` (default | primary | secondary | ghost | link), `size` (sm | md | lg), `disabled`, `loading`, `onClick`
   - **States**: default, hover, active, disabled, loading
   - **Design Tokens**: Colors, spacing, typography, shadows

2. **Card**
   - **Props**: `header`, `footer`, `children`, `variant` (default | outlined)
   - **States**: default, hover, interactive
   - **Design Tokens**: Background, border, shadow, spacing

3. **Input / Form Field**
   - **Props**: `label`, `error`, `helperText`, `required`, `disabled`
   - **States**: default, focus, error, disabled
   - **Design Tokens**: Border color, focus ring, error color

4. **Table**
   - **Props**: `columns`, `data`, `sortable`, `pagination`, `loading`, `empty`
   - **States**: loading, empty, error, populated
   - **Design Tokens**: Row hover, border, spacing

5. **Modal / Dialog**
   - **Props**: `open`, `onClose`, `title`, `description`, `footer`, `size`
   - **States**: open, closed, animating
   - **Accessibility**: Focus trap, Escape key, ARIA labels

#### Page Models

1. **Usage Page**
   - **Data**: `totalRequests`, `listingCount`, `projectedBill`, `uniqueTools`, `historicalMetrics`
   - **States**: loading, error, empty (no data), populated
   - **Components**: MetricsSummary (cards), UsageChart (line chart), InfoNotice

2. **Dashboard Layout**
   - **Data**: `user`, `organization`, `navigationItems`
   - **States**: authenticated, loading, error (redirect to login)
   - **Components**: Sidebar navigation, Header, Main content area

#### Design Tokens

```typescript
// colors, spacing, typography, shadows, borders
const designTokens = {
  colors: {
    primary: { 50: '...', 100: '...', ..., 900: '...' },
    secondary: { ... },
    success: { ... },
    error: { ... },
    warning: { ... },
  },
  spacing: { xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '32px' },
  typography: {
    fontFamily: { sans: 'Inter, system-ui', mono: 'Fira Code' },
    fontSize: { xs: '12px', sm: '14px', base: '16px', lg: '18px', xl: '20px' },
  },
  shadows: { sm: '...', md: '...', lg: '...' },
  borders: { radius: { sm: '4px', md: '8px', lg: '12px' } },
}
```

### API Contracts (`contracts/`)

**Note**: This feature does not introduce new REST API endpoints. "Contracts" here refer to **component API contracts** (TypeScript interfaces for props).

#### Component Contracts

```typescript
// contracts/components.ts

export interface ButtonProps {
  variant?: 'default' | 'primary' | 'secondary' | 'ghost' | 'link'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
  children: React.ReactNode
}

export interface CardProps {
  header?: React.ReactNode
  footer?: React.ReactNode
  children: React.ReactNode
  variant?: 'default' | 'outlined'
  className?: string
}

export interface InputProps {
  label: string
  error?: string
  helperText?: string
  required?: boolean
  disabled?: boolean
  value: string
  onChange: (value: string) => void
  type?: 'text' | 'email' | 'password' | 'number'
}

export interface TableColumn<T> {
  key: keyof T
  header: string
  render?: (value: T[keyof T], row: T) => React.ReactNode
  sortable?: boolean
}

export interface TableProps<T> {
  columns: TableColumn<T>[]
  data: T[]
  loading?: boolean
  empty?: React.ReactNode
  pagination?: {
    page: number
    pageSize: number
    total: number
    onPageChange: (page: number) => void
  }
}

export interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  footer?: React.ReactNode
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
}
```

#### Page Data Contracts

```typescript
// contracts/pages.ts

export interface UsageMetrics {
  totalRequests: number
  listingCount: number
  projectedBill: number
  uniqueTools: number
  monthYear: string
}

export interface HistoricalMetric {
  monthYear: string
  totalApiRequests: number
}

export interface UsagePageProps {
  metrics: UsageMetrics | null
  historicalMetrics: HistoricalMetric[]
  loading: boolean
  error: Error | null
}
```

### Quickstart Guide (`quickstart.md`)

```markdown
# Quickstart: Dashboard Design System

## Prerequisites

- Node.js 20+ installed
- npm or pnpm package manager
- Dashboard directory: `/dashboard`

## Installation

### 1. Install shadcn/ui

\`\`\`bash
cd dashboard
npx shadcn@latest init
\`\`\`

Follow prompts:
- **TypeScript**: Yes
- **Style**: Default
- **Base color**: Slate
- **CSS variables**: Yes
- **Tailwind config**: Yes
- **Import alias**: @/components

### 2. Install Core Components

\`\`\`bash
npx shadcn@latest add button card input table dialog skeleton badge select
\`\`\`

### 3. Install Chart Library

\`\`\`bash
npm install recharts
\`\`\`

### 4. Verify Installation

\`\`\`bash
npm run dev
\`\`\`

Visit `http://localhost:3000/dashboard/usage` - page should load without errors.

## Usage

### Import Components

\`\`\`tsx
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function MyPage() {
  return (
    <Card>
      <Button>Click me</Button>
    </Card>
  )
}
\`\`\`

### Customize Theme

Edit `tailwind.config.ts` to customize colors, spacing, typography.

## Troubleshooting

**Error: Module not found '@/components/ui/button'**
- Run `npx shadcn@latest add button` to install component

**Error: Tailwind classes not applying**
- Check `globals.css` has `@tailwind` directives
- Restart dev server: `npm run dev`
```

## Phase 2: Implementation Tasks

**Note**: Detailed tasks will be generated via `/speckit.tasks` command after this plan is complete. High-level phases:

### Phase A: Setup & Configuration (P1 - Production Blocker)

1. Diagnose usage page bug (browser console, network tab)
2. Install shadcn/ui CLI and configure
3. Install Tailwind CSS 3.x (or verify existing config)
4. Install core shadcn/ui components (Button, Card, Input, Table, Dialog, Skeleton, Badge)
5. Install chart library (Recharts)
6. Configure TypeScript paths for `@/components` alias
7. Test: Verify shadcn/ui components render correctly

### Phase B: Usage Page Fix (P1 - Production Blocker)

1. Fix usage page data fetching (Supabase queries)
2. Add loading state (skeleton loaders)
3. Add error state (error boundary + retry button)
4. Add empty state (no data messaging)
5. Implement MetricsSummary with shadcn/ui Cards
6. Implement UsageChart with Recharts
7. Test: Usage page renders without errors, displays metrics correctly

### Phase C: Dashboard Visual Polish (P1 - Production Blocker)

1. Update dashboard layout with shadcn/ui components
2. Implement consistent navigation (sidebar or top nav)
3. Apply design tokens (colors, spacing, typography) across all pages
4. Add hover states and transitions to interactive elements
5. Test: All pages render consistently, no visual errors

### Phase D: Component Library (P2 - Enhancement)

1. Create reusable Card component with variants
2. Create reusable Button component with variants
3. Create reusable Input/Form Field component
4. Create reusable Table component with sorting/pagination
5. Create reusable Modal/Dialog component
6. Document components with Storybook (optional) or comments
7. Test: Components are reusable and maintain consistency

### Phase E: Testing & Accessibility (P2 - Quality)

1. Add component tests with React Testing Library
2. Add E2E tests with Playwright (usage page flow)
3. Run Lighthouse accessibility audit
4. Fix accessibility issues (color contrast, keyboard nav, ARIA labels)
5. Test: >80% test coverage, WCAG 2.1 Level AA compliance

## Dependencies

### External Dependencies (New)

- `shadcn@latest` (CLI tool - not a runtime dependency)
- `@radix-ui/*` (installed by shadcn/ui - UI primitives)
- `class-variance-authority` (CVA - component variant system)
- `clsx` (conditional class names)
- `tailwind-merge` (merge Tailwind classes)
- `lucide-react` (icon library)
- `recharts` (charting library)
- `react-hook-form` (form management)
- `zod` (schema validation)

### Existing Dependencies (No Changes)

- Next.js 15.5.4
- React 19.1.0
- Tailwind CSS (already installed, may need reconfiguration)
- Supabase client (browser + server)
- TypeScript 5.x

### Blocking Dependencies

1. **Usage page bug diagnosis**: Must identify root cause before applying design system
2. **Tailwind CSS configuration**: Must be properly configured before installing shadcn/ui
3. **TypeScript paths**: Must configure `@/components` alias for shadcn/ui imports

## Risks & Mitigations

### Technical Risks

1. **Risk**: shadcn/ui incompatibility with Next.js 15 + React 19
   - **Likelihood**: Medium (bleeding edge versions)
   - **Impact**: High (blocks entire feature)
   - **Mitigation**: Research compatibility in Phase 0, test installation on branch, downgrade Next.js if needed

2. **Risk**: Usage page bug is backend/data issue, not frontend
   - **Likelihood**: Low (appears to be rendering issue)
   - **Impact**: Medium (requires backend fix)
   - **Mitigation**: Diagnose early in Phase 0, escalate to backend team if needed

3. **Risk**: Bundle size increases significantly with new dependencies
   - **Likelihood**: Low (shadcn/ui is tree-shakeable)
   - **Impact**: Medium (slower page loads)
   - **Mitigation**: Measure bundle size with Next.js analyzer, only install needed components

### Schedule Risks

1. **Risk**: Design system setup takes longer than expected
   - **Likelihood**: Medium (configuration complexity)
   - **Impact**: High (delays production deployment)
   - **Mitigation**: Timebox shadcn/ui setup to 4 hours, have fallback plan (manual Tailwind components)

2. **Risk**: Accessibility compliance requires significant refactoring
   - **Likelihood**: Low (shadcn/ui is accessible by default)
   - **Impact**: Medium (delays polish phase)
   - **Mitigation**: Run Lighthouse early, prioritize high-impact fixes (color contrast, keyboard nav)

## Success Metrics

Metrics from feature spec (repeated here for easy reference):

- **SC-001**: 100% of dashboard pages render without visual errors
- **SC-002**: Usage page loads in <2 seconds
- **SC-003**: 100% of components use design system tokens
- **SC-004**: Interactive elements respond in <100ms
- **SC-005**: Dashboard works on 320px-2560px viewport widths
- **SC-006**: 95% task completion rate (view usage, generate key, check billing)
- **SC-007**: WCAG 2.1 Level AA compliance (Lighthouse score >90)
- **SC-008**: Developers build new pages 50% faster with component library

## Next Steps

1. **Review this plan** for technical accuracy and completeness
2. **Run Phase 0 research** to resolve NEEDS CLARIFICATION items (if any)
3. **Run Phase 1 design** to create data-model.md and contracts/
4. **Run `/speckit.tasks`** to generate actionable task breakdown
5. **Begin implementation** starting with P1 tasks (usage page fix + design system setup)

---

**Status**: ✅ **PLAN READY**
**Phase**: Planning Complete → Awaiting `/speckit.tasks` for task generation
**Branch**: `004-we-need-to`
**Next Command**: `/speckit.tasks` to break down implementation into concrete tasks
