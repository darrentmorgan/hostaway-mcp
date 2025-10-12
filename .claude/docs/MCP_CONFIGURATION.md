# MCP Configuration Guide

## Current Architecture: Direct Access (All MCP Servers Loaded)

**Status**: Active as of 2025-01-12

All MCP servers are loaded globally in every Claude Code session. This provides immediate access to all tools without delegation overhead.

---

## Global MCP Servers

**Configuration File**: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Active MCP Servers (6 total)

| MCP Server | Status | Purpose | Tools Prefix |
|------------|--------|---------|--------------|
| **playwright** | ✅ Active | Browser automation, E2E testing | `mcp__plugin_testing-suite_playwright-server__*` |
| **Context7** | ✅ Active | Supabase documentation search | `mcp__plugin_supabase-toolkit_supabase__search_docs` |
| **supabase** | ⚠️ Needs Token | Database operations, migrations | `mcp__plugin_supabase-toolkit_supabase__*` |
| **firecrawl-mcp** | ✅ Configured | Web scraping, content extraction | `mcp__firecrawl__*` |
| **clickup** | ✅ Configured | Task management, project tracking | `mcp__clickup__*` |
| **chrome-devtools** | ⚠️ Legacy | (Superseded by Playwright) | N/A |

### Notes

1. **Browser Automation**: Uses **Playwright MCP**, not chrome-devtools
   - Agent configs may reference "chrome-devtools" but actual implementation is Playwright
   - Tool names: `mcp__plugin_testing-suite_playwright-server__navigate`, `__click`, etc.

2. **Supabase Database**: Requires valid access token
   - Current token may be expired (Unauthorized errors)
   - Generate new token at: https://supabase.com/dashboard
   - Project ref: `khodniyhethjyomscyjw`

3. **Context7**: Working for documentation search
   - Successfully searches Supabase docs
   - Tool: `mcp__plugin_supabase-toolkit_supabase__search_docs`

---

## Project Configuration

All projects inherit global MCP configuration via `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__chrome-devtools",        // Legacy naming (actually Playwright)
      "mcp__supabase",                // Database operations
      "mcp__clickup",                 // Task management
      "mcp__firecrawl-mcp",           // Web scraping
      "mcp__Context7",                // Documentation search
      "mcp__ide"                      // IDE integration
    ]
  }
}
```

**No per-project MCP configuration** - all projects use global config.

---

## Agent MCP Access

### How Agents Access MCP Tools

**Current Model**: Direct access from main session
- Main orchestrator has all MCP tools loaded
- Sub-agents launched via Task tool do NOT inherit MCP access
- All MCP operations must be performed by main session

### Agent Specializations

| Agent | MCP Focus | Documentation |
|-------|-----------|---------------|
| qa-expert | Playwright browser automation | `.claude/agents/configs/qa-expert.json` |
| backend-architect | Supabase database operations | `.claude/agents/configs/backend-architect.json` |
| database-optimizer | Supabase query optimization | `.claude/agents/configs/database-optimizer.json` |
| documentation-expert | Context7 docs search | `.claude/agents/configs/documentation-expert.json` |
| web-scraper | Firecrawl web scraping | `.claude/agents/configs/web-scraper.json` |
| product-manager | ClickUp task management | `.claude/agents/configs/product-manager.json` |

**Note**: Agent configs specify intended MCP servers, but main session performs actual MCP operations.

---

## Troubleshooting

### Supabase Unauthorized Error

**Error**: `Unauthorized. Please provide a valid access token`

**Solution**:
1. Go to https://supabase.com/dashboard
2. Navigate to your project: `khodniyhethjyomscyjw`
3. Settings → API → Generate new access token
4. Update `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   "supabase": {
     "env": {
       "SUPABASE_ACCESS_TOKEN": "YOUR_NEW_TOKEN"
     }
   }
   ```
5. Restart Claude Code

### Chrome DevTools Not Found

**Issue**: Agent configs reference `mcp__chrome-devtools` but tools not available

**Explanation**: Browser automation uses **Playwright**, not chrome-devtools
- Tool prefix: `mcp__plugin_testing-suite_playwright-server__`
- Permissions labeled as `mcp__chrome-devtools` for backwards compatibility
- No action needed - Playwright handles all browser automation

### MCP Tools Not Available in Sub-Agents

**Issue**: Task tool sub-agents report no MCP access

**Explanation**: Sub-agents don't inherit MCP from main session
- Only main orchestrator has MCP tools
- Perform MCP operations directly in main session
- Sub-agents provide planning/analysis only

---

## Context Usage

**Estimated Token Usage**:
- All 6 MCP servers: ~125k tokens
- Without MCP: ~50k tokens base

**Impact**: 75k additional tokens for MCP context

**Trade-off**: Immediate tool access vs token efficiency

---

## Future Optimization

If context limits become an issue, consider:

1. **Remove unused MCP servers** from global config
2. **Selective loading** based on project type
3. **Delegation architecture** (requires Claude platform support)

See `.claude/agents/mcp-mapping.json` for delegation design (currently not active).

---

## Configuration Files Reference

### Global
- `~/Library/Application Support/Claude/claude_desktop_config.json` - Active MCP config

### Per-Project
- `.claude/settings.local.json` - Permissions (inherits global MCP)
- `.claude/agents/mcp-mapping.json` - Agent→MCP mapping (documentation only)
- `.claude/agents/configs/*.json` - Agent MCP preferences (guidance only)

### Documentation Only (Not Active)
- `.claude/claude_desktop_config_orchestrator.json` - Delegation design reference
- `.claude/docs/MCP_DELEGATION_GUIDE.md` - Not created (delegation not active)

---

## Last Updated

2025-01-12 - Documented actual architecture after MCP testing
