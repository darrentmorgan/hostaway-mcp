/**
 * Error fixture generator
 *
 * Generates error responses for testing error hygiene
 */

/**
 * Generate a large HTML error page
 *
 * Simulates the kind of oversized error response that can come
 * from upstream APIs and should be stripped by error hygiene.
 *
 * @returns Large HTML error string (>10KB)
 */
export function generateLargeHtmlError(): string {
  const htmlTemplate = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>500 Internal Server Error</title>
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
      padding: 20px;
    }
    .error-container {
      background: white;
      border-radius: 10px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      padding: 40px;
      max-width: 800px;
      width: 100%;
    }
    h1 {
      color: #e74c3c;
      font-size: 48px;
      margin: 0 0 20px 0;
    }
    p {
      color: #555;
      font-size: 18px;
      line-height: 1.6;
    }
    .stack-trace {
      background: #f8f9fa;
      border: 1px solid #dee2e6;
      border-radius: 5px;
      padding: 20px;
      margin-top: 30px;
      font-family: 'Courier New', monospace;
      font-size: 14px;
      overflow-x: auto;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .error-code {
      background: #e74c3c;
      color: white;
      padding: 5px 10px;
      border-radius: 3px;
      font-weight: bold;
      display: inline-block;
      margin-bottom: 20px;
    }
  </style>
</head>
<body>
  <div class="error-container">
    <div class="error-code">ERROR 500</div>
    <h1>Internal Server Error</h1>
    <p>We're sorry, but something went wrong on our end. Our team has been notified and is working to fix the issue.</p>
    <p>Please try again later. If the problem persists, contact support with the error ID below.</p>
    <p><strong>Error ID:</strong> ERR-${Date.now()}-${Math.random().toString(36).substring(7)}</p>

    <div class="stack-trace">
Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/fastapi/applications.py", line 271, in __call__
    await super().__call__(scope, receive, send)
  File "/usr/local/lib/python3.11/site-packages/starlette/applications.py", line 122, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 184, in __call__
    raise exc
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 162, in __call__
    await self.app(scope, receive, _send)
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 79, in __call__
    raise exc
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 68, in __call__
    await self.app(scope, receive, sender)
  File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 718, in __call__
    await route.handle(scope, receive, send)
  File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 276, in handle
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 69, in app
    await response(scope, receive, send)
  File "/app/src/api/routes/listings.py", line 145, in get_listings
    result = await client.get_listings(limit=limit, offset=offset)
  File "/app/src/services/hostaway_client.py", line 234, in get_listings
    response = await self._request("GET", "/v1/listings", params=params)
  File "/app/src/services/hostaway_client.py", line 89, in _request
    response.raise_for_status()
  File "/usr/local/lib/python3.11/site-packages/httpx/_models.py", line 761, in raise_for_status
    raise HTTPStatusError(message, request=request, response=self)
httpx.HTTPStatusError: Server error '500 Internal Server Error' for url 'https://api.hostaway.com/v1/listings?limit=50&offset=0'

${Array.from({ length: 100 }, (_, i) => `Additional context line ${i + 1}: Lorem ipsum dolor sit amet, consectetur adipiscing elit.`).join('\n')}
    </div>
  </div>
</body>
</html>
  `;

  return htmlTemplate;
}

/**
 * Generate a compact JSON error (what we want after error hygiene)
 *
 * @param options - Error configuration
 * @returns Compact JSON error object
 */
export function generateCompactJsonError(options: {
  error: string;
  message: string;
  correlationId?: string;
  statusCode?: number;
} = {
  error: 'Internal server error',
  message: 'An unexpected error occurred',
}): {
  error: string;
  message: string;
  correlationId: string;
  statusCode?: number;
} {
  return {
    ...options,
    correlationId: options.correlationId || `ERR-${Date.now()}-${Math.random().toString(36).substring(7)}`,
  };
}
