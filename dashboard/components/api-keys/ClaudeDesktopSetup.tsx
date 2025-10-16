'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface ClaudeDesktopSetupProps {
  apiKey: string | null
  serverUrl: string
}

export default function ClaudeDesktopSetup({ apiKey, serverUrl }: ClaudeDesktopSetupProps) {
  const [copied, setCopied] = useState(false)
  const [platform, setPlatform] = useState<'macos' | 'windows' | 'linux'>('macos')

  const configPaths = {
    macos: '~/Library/Application Support/Claude/claude_desktop_config.json',
    windows: '%APPDATA%\\Claude\\claude_desktop_config.json',
    linux: '~/.config/Claude/claude_desktop_config.json'
  }

  // Show masked key (we don't have the full key, only the hash)
  const displayKey = apiKey ? `mcp_${apiKey.slice(-8)}...` : 'YOUR_API_KEY_HERE'
  const hasKey = apiKey !== null

  const config = `{
  "mcpServers": {
    "hostaway-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "hostaway-mcp-client"
      ],
      "env": {
        "REMOTE_MCP_URL": "${serverUrl}",
        "REMOTE_MCP_API_KEY": "${hasKey ? 'YOUR_SAVED_API_KEY' : 'YOUR_API_KEY_HERE'}"
      }
    }
  }
}`

  const handleCopy = async () => {
    await navigator.clipboard.writeText(config)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const hasActiveKey = apiKey !== null

  return (
    <Card>
      <CardHeader>
        <CardTitle>Claude Desktop Setup</CardTitle>
        <CardDescription>
          Add the Hostaway MCP server to your Claude Desktop configuration
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Platform Selector */}
        <div>
          <label className="block text-sm font-medium mb-2">Select your platform:</label>
          <div className="flex gap-2">
            {(['macos', 'windows', 'linux'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPlatform(p)}
                className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                  platform === p
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {p === 'macos' ? 'macOS' : p === 'windows' ? 'Windows' : 'Linux'}
              </button>
            ))}
          </div>
        </div>

        {/* Key Notice */}
        {hasActiveKey && (
          <Alert>
            <AlertDescription className="text-sm">
              <strong>Note:</strong> Replace <code className="px-1 py-0.5 bg-gray-200 rounded text-xs">YOUR_SAVED_API_KEY</code> in the configuration below with the API key you saved when you generated it.
              For security, we don&apos;t display full keys after generation.
            </AlertDescription>
          </Alert>
        )}

        {/* Instructions */}
        <div className="space-y-2">
          <h3 className="font-medium">Setup Instructions:</h3>
          <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
            <li>
              Open your Claude Desktop config file at:{' '}
              <code className="px-2 py-1 bg-gray-100 rounded text-xs">{configPaths[platform]}</code>
            </li>
            <li>Add the configuration below to your config file</li>
            <li>Replace <code className="px-1 py-0.5 bg-gray-200 rounded text-xs">YOUR_SAVED_API_KEY</code> with your actual API key</li>
            <li>If you already have other MCP servers, add this inside the existing &quot;mcpServers&quot; section</li>
            <li>Save the file and restart Claude Desktop</li>
          </ol>
        </div>

        {/* Configuration */}
        <div className="relative">
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-medium">Configuration:</label>
            <button
              onClick={handleCopy}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              {copied ? '✓ Copied!' : 'Copy'}
            </button>
          </div>
          <pre className="p-4 bg-gray-50 rounded-lg overflow-x-auto text-xs border">
            <code>{config}</code>
          </pre>
        </div>

        {/* Warning */}
        <Alert>
          <AlertDescription className="text-sm">
            <strong>Important:</strong> After adding this configuration, restart Claude Desktop completely for the changes to take effect.
          </AlertDescription>
        </Alert>

        {/* Verification */}
        <div className="space-y-2">
          <h3 className="font-medium text-sm">Verify Installation:</h3>
          <p className="text-sm text-muted-foreground">
            After restarting Claude Desktop, you should see &quot;hostaway-mcp&quot; in the MCP servers list in the bottom-right corner of the app.
            You can then use Hostaway tools directly in your conversations.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
