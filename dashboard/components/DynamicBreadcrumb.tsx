'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'

// Map of paths to readable labels
const pathLabels: Record<string, string> = {
  '': 'Home',
  'usage': 'Usage',
  'billing': 'Billing',
  'api-keys': 'API Keys',
  'settings': 'Settings',
}

function formatPathSegment(segment: string): string {
  // Check if we have a custom label
  if (pathLabels[segment]) {
    return pathLabels[segment]
  }

  // Otherwise, capitalize and replace hyphens with spaces
  return segment
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export function DynamicBreadcrumb() {
  const pathname = usePathname()

  // Skip breadcrumbs on home page or auth pages
  if (pathname === '/' || pathname.startsWith('/login') || pathname.startsWith('/signup')) {
    return null
  }

  // Parse pathname into segments
  const segments = pathname.split('/').filter(Boolean)

  // Build breadcrumb items
  const breadcrumbItems = segments.map((segment, index) => {
    const href = '/' + segments.slice(0, index + 1).join('/')
    const label = formatPathSegment(segment)
    const isLast = index === segments.length - 1

    return {
      href,
      label,
      isLast,
    }
  })

  return (
    <Breadcrumb>
      <BreadcrumbList>
        {/* Home link */}
        <BreadcrumbItem>
          <BreadcrumbLink asChild>
            <Link href="/">Home</Link>
          </BreadcrumbLink>
        </BreadcrumbItem>

        {breadcrumbItems.length > 0 && <BreadcrumbSeparator />}

        {/* Dynamic segments */}
        {breadcrumbItems.map((item) => (
          <div key={item.href} className="flex items-center gap-1.5">
            <BreadcrumbItem>
              {item.isLast ? (
                <BreadcrumbPage>{item.label}</BreadcrumbPage>
              ) : (
                <BreadcrumbLink asChild>
                  <Link href={item.href}>{item.label}</Link>
                </BreadcrumbLink>
              )}
            </BreadcrumbItem>

            {!item.isLast && <BreadcrumbSeparator />}
          </div>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  )
}
