/**
 * HTTP client wrapper for testing FastAPI endpoints
 *
 * Spawns the Hostaway FastAPI server and provides methods to:
 * - Call API endpoints via HTTP
 * - Estimate token usage
 * - Manage server lifecycle
 */

import { spawn, ChildProcess } from 'child_process';
import { estimateTokens } from './tokenEstimator.js';

export interface HTTPClientOptions {
  /** Environment variables to pass to the server */
  env?: Record<string, string>;
  /** Server startup timeout in ms */
  timeout?: number;
  /** Port to run server on (default: random) */
  port?: number;
}

export interface ToolCallResult<T = unknown> {
  /** API response content */
  content: T;
  /** Estimated token count for the response */
  estimatedTokens: number;
  /** Whether the response indicates an error */
  isError: boolean;
  /** Error message if isError is true */
  errorMessage?: string;
}

/**
 * HTTP client for testing FastAPI endpoints
 *
 * Manages the lifecycle of a FastAPI server process and provides
 * type-safe methods for calling endpoints and estimating token usage.
 */
export class HTTPTestClient {
  private process?: ChildProcess;
  private baseUrl?: string;
  private options: HTTPClientOptions;

  constructor(options: HTTPClientOptions = {}) {
    this.options = {
      timeout: 10000,
      port: 0, // Random port
      ...options,
    };
  }

  /**
   * Start the FastAPI server process
   */
  async start(): Promise<void> {
    if (this.process) {
      throw new Error('Server already started');
    }

    // Load .env file from project root
    const projectRoot = process.cwd().replace('/test', '');
    const envPath = `${projectRoot}/.env`;
    const envFile = await import('fs').then(fs => fs.promises.readFile(envPath, 'utf-8'));
    const envVars: Record<string, string> = {};
    for (const line of envFile.split('\n')) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        if (key && valueParts.length > 0) {
          envVars[key.trim()] = valueParts.join('=').trim();
        }
      }
    }

    // Merge test environment with custom env vars and .env file
    const filteredEnv: Record<string, string> = {};
    for (const [key, value] of Object.entries(process.env)) {
      if (value !== undefined) {
        filteredEnv[key] = value;
      }
    }
    const env: Record<string, string> = {
      ...filteredEnv,
      ...envVars,  // Add .env vars
      ...(this.options.env || {}),  // Custom test env vars override
    };
    // Spawn the FastAPI server process
    const venvPython = projectRoot + '/.venv/bin/python';
    this.process = spawn(
      venvPython,
      ['-m', 'uvicorn', 'src.api.main:app', '--host', '127.0.0.1', '--port', String(this.options.port)],
      {
        env,
        cwd: projectRoot,
        stdio: ['ignore', 'pipe', 'pipe'],
      }
    );

    // Capture server output to extract port
    let serverOutput = '';
    this.process.stdout?.on('data', (data) => {
      serverOutput += data.toString();
    });

    this.process.stderr?.on('data', (data) => {
      serverOutput += data.toString();
    });

    // Handle process errors
    this.process.on('error', (error) => {
      throw new Error(`Failed to start server: ${error.message}`);
    });

    // Wait for server to be ready
    const startTime = Date.now();
    while (Date.now() - startTime < this.options.timeout!) {
      // Look for "Uvicorn running on" in output
      const match = serverOutput.match(/Uvicorn running on http:\/\/127\.0\.0\.1:(\d+)/);
      if (match) {
        const port = match[1];
        this.baseUrl = `http://127.0.0.1:${port}`;

        // Verify server is responding
        try {
          const response = await fetch(`${this.baseUrl}/`);
          if (response.ok) {
            return; // Server is ready
          }
        } catch {
          // Server not ready yet
        }
      }

      await new Promise((resolve) => setTimeout(resolve, 100));
    }

    throw new Error(`Server failed to start within ${this.options.timeout}ms. Output: ${serverOutput}`);
  }

  /**
   * Call an API endpoint and return the result with token estimation
   */
  async callEndpoint<T = unknown>(method: string, path: string, params?: Record<string, unknown>): Promise<ToolCallResult<T>> {
    if (!this.baseUrl) {
      throw new Error('Server not started. Call start() first.');
    }

    try {
      // Build URL with query parameters
      const url = new URL(`${this.baseUrl}${path}`);
      if (params) {
        for (const [key, value] of Object.entries(params)) {
          if (value !== undefined && value !== null) {
            url.searchParams.append(key, String(value));
          }
        }
      }

      const response = await fetch(url.toString(), {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'mcp_test_GZeJlFu9ynoCLIFPHPB3vwyHNdjRz3o53d8bvZz7sfw',
        },
      });

      const contentText = await response.text();
      const estimatedTokens = estimateTokens(contentText);
      const isError = !response.ok;

      return {
        content: JSON.parse(contentText) as T,
        estimatedTokens,
        isError,
        errorMessage: isError ? contentText : undefined,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return {
        content: {} as T,
        estimatedTokens: estimateTokens(errorMessage),
        isError: true,
        errorMessage,
      };
    }
  }

  /**
   * Stop the server process and cleanup
   */
  async stop(): Promise<void> {
    if (this.process) {
      this.process.kill('SIGTERM');

      // Wait for graceful shutdown (max 5 seconds)
      await new Promise<void>((resolve) => {
        const timeout = setTimeout(() => {
          // Force kill if not shutdown gracefully
          if (this.process) {
            this.process.kill('SIGKILL');
          }
          resolve();
        }, 5000);

        this.process!.on('exit', () => {
          clearTimeout(timeout);
          resolve();
        });
      });
    }

    this.process = undefined;
    this.baseUrl = undefined;
  }
}
