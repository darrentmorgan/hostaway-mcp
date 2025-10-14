import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface ErrorStateProps {
  error: string
  title?: string
  onRetry?: () => void
}

export default function ErrorState({
  error,
  title = 'Unable to Load Usage Data',
  onRetry,
}: ErrorStateProps) {
  // Determine if this is an authentication error
  const isAuthError = error.toLowerCase().includes('not authenticated') ||
                      error.toLowerCase().includes('organization not found')

  // Determine if this is a network/connection error
  const isNetworkError = error.toLowerCase().includes('network') ||
                         error.toLowerCase().includes('fetch') ||
                         error.toLowerCase().includes('connection')

  return (
    <Card>
      <CardHeader>
        <CardTitle>Usage Overview</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Alert variant="destructive">
            <AlertTitle>{title}</AlertTitle>
            <AlertDescription className="mt-2">
              {error}
            </AlertDescription>
          </Alert>

          <div className="rounded-lg border border-border bg-muted/50 p-6">
            <h4 className="mb-3 font-medium">What you can try:</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              {isAuthError && (
                <>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5">•</span>
                    <span>Make sure you&apos;re logged in to your account</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5">•</span>
                    <span>Check that your organization membership is active</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5">•</span>
                    <span>Try logging out and logging back in</span>
                  </li>
                </>
              )}
              {isNetworkError && (
                <>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5">•</span>
                    <span>Check your internet connection</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5">•</span>
                    <span>Try refreshing the page</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5">•</span>
                    <span>Wait a moment and try again</span>
                  </li>
                </>
              )}
              {!isAuthError && !isNetworkError && (
                <>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5">•</span>
                    <span>Refresh the page to try again</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5">•</span>
                    <span>Check if the issue persists</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5">•</span>
                    <span>Contact support if the problem continues</span>
                  </li>
                </>
              )}
            </ul>

            {onRetry && (
              <div className="mt-4">
                <Button onClick={onRetry} variant="outline" size="sm">
                  Try Again
                </Button>
              </div>
            )}
          </div>

          {!isAuthError && (
            <p className="text-xs text-muted-foreground">
              If this problem persists, please contact support with the error
              message above.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
