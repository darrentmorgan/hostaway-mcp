/**
 * MCP stdio client wrapper for testing
 *
 * Spawns the Hostaway MCP server process and provides methods to:
 * - Call MCP tools
 * - List available tools and resources
 * - Read MCP resources
 * - Estimate token usage
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { estimateTokens } from './tokenEstimator.js';

export interface MCPClientOptions {
  /** Environment variables to pass to the MCP server */
  env?: Record<string, string>;
  /** Server startup timeout in ms */
  timeout?: number;
  /** Python command to use (default: 'python3') */
  pythonCommand?: string;
}

export interface ToolCallResult<T = unknown> {
  /** Tool response content */
  content: T;
  /** Estimated token count for the response */
  estimatedTokens: number;
  /** Whether the response indicates an error */
  isError: boolean;
  /** Error message if isError is true */
  errorMessage?: string;
}

/**
 * MCP client for testing
 *
 * Manages the lifecycle of an MCP server process and provides
 * type-safe methods for calling tools and estimating token usage.
 */
export class MCPTestClient {
  private client?: Client;
  private transport?: StdioClientTransport;
  private options: MCPClientOptions;

  constructor(options: MCPClientOptions = {}) {
    // Use virtual environment python by default
    const venvPython = process.cwd().replace('/test', '') + '/.venv/bin/python';

    this.options = {
      timeout: 10000,
      pythonCommand: venvPython,
      ...options,
    };
  }

  /**
   * Start the MCP server process and connect
   */
  async start(): Promise<void> {
    if (this.client) {
      throw new Error('MCP server already started');
    }

    // Merge test environment with custom env vars
    // Filter out undefined values from process.env
    const filteredEnv: Record<string, string> = {};
    for (const [key, value] of Object.entries(process.env)) {
      if (value !== undefined) {
        filteredEnv[key] = value;
      }
    }
    const env: Record<string, string> = {
      ...filteredEnv,
      ...(this.options.env || {}),
    };

    // Get project root directory
    const projectRoot = process.cwd().replace('/test', '');

    // Create stdio transport using mcp CLI (this handles spawning the process)
    this.transport = new StdioClientTransport({
      command: projectRoot + '/.venv/bin/mcp',
      args: ['run', 'src/api/main.py:mcp', '--transport', 'stdio'],
      env,
      cwd: projectRoot,
    });

    // Create MCP client
    this.client = new Client(
      {
        name: 'hostaway-mcp-test-client',
        version: '1.0.0',
      },
      {
        capabilities: {},
      }
    );

    // Connect client to transport
    await this.client.connect(this.transport);

    // Wait for server to be ready (simple health check via listing tools)
    const startTime = Date.now();
    while (Date.now() - startTime < this.options.timeout!) {
      try {
        await this.client.listTools();
        return; // Server is ready
      } catch (error) {
        // Server not ready yet, wait a bit
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
    }

    throw new Error(`MCP server failed to start within ${this.options.timeout}ms`);
  }

  /**
   * Call an MCP tool and return the result with token estimation
   */
  async callTool<T = unknown>(toolName: string, args: Record<string, unknown> = {}): Promise<ToolCallResult<T>> {
    if (!this.client) {
      throw new Error('MCP client not started. Call start() first.');
    }

    try {
      const result = await this.client.callTool({
        name: toolName,
        arguments: args,
      });

      // Extract content from result
      const contentArray = result.content as Array<{ text?: string }>;
      const contentItem = contentArray[0];
      const contentText = contentItem?.text ?? JSON.stringify(result.content);
      const estimatedTokens = estimateTokens(contentText);

      // Check if response indicates an error
      const isError = Boolean(result.isError);
      const errorMessage = isError ? contentText : undefined;

      return {
        content: JSON.parse(contentText) as T,
        estimatedTokens,
        isError,
        errorMessage,
      };
    } catch (error) {
      // Handle client-side errors
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
   * List available MCP tools
   */
  async listTools(): Promise<Array<{ name: string; description?: string }>> {
    if (!this.client) {
      throw new Error('MCP client not started. Call start() first.');
    }

    const result = await this.client.listTools();
    return result.tools.map((tool) => ({
      name: tool.name,
      description: tool.description,
    }));
  }

  /**
   * List available MCP resources
   */
  async listResources(): Promise<Array<{ uri: string; name?: string }>> {
    if (!this.client) {
      throw new Error('MCP client not started. Call start() first.');
    }

    const result = await this.client.listResources();
    return result.resources.map((resource) => ({
      uri: resource.uri,
      name: resource.name,
    }));
  }

  /**
   * Read an MCP resource
   */
  async readResource(uri: string): Promise<{ content: string; estimatedTokens: number }> {
    if (!this.client) {
      throw new Error('MCP client not started. Call start() first.');
    }

    const result = await this.client.readResource({ uri });
    const contentItem = result.contents[0] as { text?: string } | undefined;
    const content = contentItem?.text ?? JSON.stringify(result.contents);
    const estimatedTokens = estimateTokens(content);

    return {
      content,
      estimatedTokens,
    };
  }

  /**
   * Stop the MCP server process and cleanup
   */
  async stop(): Promise<void> {
    try {
      // Close client connection (this also closes the transport and kills the process)
      if (this.client && this.transport) {
        await this.client.close();
      }
    } finally {
      this.client = undefined;
      this.transport = undefined;
    }
  }
}
