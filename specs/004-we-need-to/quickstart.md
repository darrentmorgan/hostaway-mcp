# Quickstart Guide: Dashboard Design System Setup

**Date**: 2025-10-14
**Feature**: Production-Ready Dashboard with Design System
**Phase**: 1 (Design & Contracts)

## Prerequisites

Before starting implementation, ensure you have:

- ✅ Node.js 18+ installed (`node --version`)
- ✅ npm or pnpm installed (`npm --version`)
- ✅ Next.js 15.5.4 with React 19.1.0 (already in project)
- ✅ TypeScript 5.x configured (already in project)
- ✅ Git repository initialized (already in project)

---

## Step 1: Install shadcn/ui CLI

shadcn/ui is not installed via npm. Instead, you use the CLI to copy components directly into your project.

```bash
cd dashboard
npx shadcn@latest init
```

**CLI Prompts**:
```
Would you like to use TypeScript? › Yes
Which style would you like to use? › Default
Which color would you like to use as base color? › Slate
Where is your global CSS file? › app/globals.css
Would you like to use CSS variables for colors? › Yes
Are you using a custom tailwind prefix? › No
Where is your tailwind.config.js located? › tailwind.config.ts
Configure the import alias for components: › @/components
Configure the import alias for utils: › @/lib/utils
Are you using React Server Components? › Yes
Write configuration to components.json? › Yes
```

**What This Does**:
- Updates `tailwind.config.ts` with shadcn/ui theme tokens
- Creates `components.json` (shadcn/ui configuration)
- Adds CSS variables to `app/globals.css`
- Creates `lib/utils.ts` with `cn()` helper function
- Configures TypeScript path aliases

---

## Step 2: Verify Tailwind CSS Configuration

After running `npx shadcn@latest init`, your `tailwind.config.ts` should look like this:

```typescript
import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
```

---

## Step 3: Verify CSS Variables in `app/globals.css`

Your `app/globals.css` should now include CSS variables:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;

    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;

    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;

    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;

    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;

    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;

    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;

    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;

    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;

    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;

    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;

    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;

    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;

    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;

    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;

    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;

    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;

    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

---

## Step 4: Install Core Components

Install the base components needed for the dashboard:

```bash
# Install Button component
npx shadcn@latest add button

# Install Card component
npx shadcn@latest add card

# Install Input component
npx shadcn@latest add input

# Install Table component
npx shadcn@latest add table

# Install Dialog (Modal) component
npx shadcn@latest add dialog

# Install Skeleton component
npx shadcn@latest add skeleton

# Install Alert component
npx shadcn@latest add alert

# Install Badge component
npx shadcn@latest add badge

# Install Select component
npx shadcn@latest add select

# Install Tooltip component
npx shadcn@latest add tooltip
```

**What This Does**:
- Creates component files in `components/ui/`
- Each component is a self-contained TypeScript file
- Components are fully customizable (they live in your codebase, not node_modules)

**Verify Installation**:
```bash
ls components/ui/
# Should see: button.tsx, card.tsx, input.tsx, table.tsx, dialog.tsx, skeleton.tsx, alert.tsx, badge.tsx, select.tsx, tooltip.tsx
```

---

## Step 5: Install Recharts for Usage Page Charts

```bash
npm install recharts
npm install --save-dev @types/recharts
```

**What This Does**:
- Installs Recharts charting library (~95kb)
- Adds TypeScript type definitions

---

## Step 6: Create Component Folders

Organize page-specific components:

```bash
mkdir -p components/usage
mkdir -p components/billing
mkdir -p components/api-keys
mkdir -p components/settings
```

---

## Step 7: Verify TypeScript Configuration

Ensure `tsconfig.json` includes path aliases (should already be configured):

```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

This allows imports like:
```typescript
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
```

---

## Step 8: Test Installation

Create a test page to verify setup:

```typescript
// app/test-design-system/page.tsx
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export default function TestPage() {
  return (
    <div className="container mx-auto p-8">
      <Card>
        <CardHeader>
          <CardTitle>Design System Test</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Button variant="default">Default Button</Button>
            <Button variant="primary">Primary Button</Button>
            <Button variant="secondary">Secondary Button</Button>
            <Button variant="destructive">Destructive Button</Button>
            <Button variant="ghost">Ghost Button</Button>
            <Button variant="link">Link Button</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
```

**Run Test**:
```bash
npm run dev
# Navigate to http://localhost:3000/test-design-system
```

**Expected Result**:
- Card with white background, border, rounded corners
- 6 buttons with different variants
- Buttons show hover states (background darkens)

---

## Step 9: Install Development Tools (Optional but Recommended)

### Prettier + Tailwind Plugin (Code Formatting)

```bash
npm install --save-dev prettier prettier-plugin-tailwindcss
```

Create `.prettierrc`:
```json
{
  "plugins": ["prettier-plugin-tailwindcss"],
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5"
}
```

### ESLint Tailwind Plugin (Linting)

```bash
npm install --save-dev eslint-plugin-tailwindcss
```

Update `.eslintrc.json`:
```json
{
  "extends": ["next/core-web-vitals", "plugin:tailwindcss/recommended"],
  "plugins": ["tailwindcss"]
}
```

---

## Step 10: Accessibility Testing Setup

### Install Lighthouse CI

```bash
npm install --save-dev @lhci/cli
```

Create `.lighthouserc.json`:
```json
{
  "ci": {
    "collect": {
      "startServerCommand": "npm run build && npm run start",
      "url": ["http://localhost:3000/usage", "http://localhost:3000/billing"],
      "numberOfRuns": 3
    },
    "assert": {
      "assertions": {
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "categories:performance": ["warn", { "minScore": 0.8 }]
      }
    }
  }
}
```

**Run Lighthouse**:
```bash
npm run build
npm run start
npx lhci autorun
```

### Install axe-core for E2E Tests (Playwright)

```bash
npm install --save-dev @axe-core/playwright
```

---

## Step 11: Add Scripts to `package.json`

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "format": "prettier --write \"**/*.{ts,tsx,js,jsx,json,md}\"",
    "test:a11y": "lhci autorun",
    "test:e2e": "playwright test"
  }
}
```

---

## Common Issues & Troubleshooting

### Issue 1: `Module not found: Can't resolve '@/components/ui/button'`

**Solution**: Verify TypeScript path aliases in `tsconfig.json`:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

Restart TypeScript server in your editor (VS Code: `Cmd+Shift+P` → "Restart TS Server").

---

### Issue 2: CSS variables not applying (components look unstyled)

**Solution**: Verify `app/globals.css` is imported in root layout:
```typescript
// app/layout.tsx
import './globals.css'
```

Check browser DevTools (Inspect Element → Computed Styles) to see if CSS variables are defined.

---

### Issue 3: shadcn/ui CLI fails with "Could not resolve tailwind.config.ts"

**Solution**: Ensure Tailwind CSS is installed:
```bash
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Then rerun `npx shadcn@latest init`.

---

### Issue 4: Recharts not rendering (blank chart area)

**Solution**: Ensure `ResponsiveContainer` is used and has explicit width/height:
```tsx
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data}>
    {/* Chart components */}
  </LineChart>
</ResponsiveContainer>
```

Check browser console for errors (missing data, incorrect data format).

---

## Next Steps

After completing this setup:

1. ✅ shadcn/ui is installed and configured
2. ✅ Tailwind CSS is configured with CSS variables
3. ✅ Base components are available in `components/ui/`
4. ✅ Recharts is installed for usage page charts
5. ✅ Accessibility testing tools are configured

**Ready to implement**:
- Create page-specific components (MetricsSummary, UsageChart)
- Apply design system to existing dashboard pages
- Fix usage page rendering issues
- Run accessibility tests

See `contracts/` directory for component prop interfaces and usage examples.

---

## Reference Links

- **shadcn/ui Docs**: https://ui.shadcn.com/docs
- **Tailwind CSS Docs**: https://tailwindcss.com/docs
- **Radix UI Docs**: https://www.radix-ui.com/docs/primitives
- **Recharts Docs**: https://recharts.org/en-US/guide
- **Next.js App Router**: https://nextjs.org/docs/app
- **Lighthouse CI**: https://github.com/GoogleChrome/lighthouse-ci
- **axe-core**: https://www.deque.com/axe/

---

**Status**: ✅ **QUICKSTART COMPLETE**
**Date**: 2025-10-14
**Next Phase**: Create component contracts (TypeScript interfaces)
