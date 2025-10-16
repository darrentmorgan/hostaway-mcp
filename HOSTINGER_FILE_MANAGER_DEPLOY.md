# Deploy via Hostinger File Manager (No SSH Required)

## Step 1: Extract the Package Locally

```bash
cd /tmp
mkdir hostaway-mcp-extracted
cd hostaway-mcp-extracted
tar -xzf /tmp/hostaway-mcp-deploy.tar.gz
```

## Step 2: Upload via Hostinger File Manager

1. Login to Hostinger control panel: https://www.hostinger.com/cpanel-login
2. Go to **File Manager**
3. Navigate to `/home/u631126255/hostaway-mcp/`
4. Create backup folder: `backup-$(date +%Y%m%d)` and move current `src/` there
5. Upload the following files from `/tmp/hostaway-mcp-extracted/`:
   - `src/` folder (entire directory)
   - `pyproject.toml`
   - `mcp_stdio_server.py`

## Step 3: Update Environment Variables

In File Manager:
1. Navigate to `/home/u631126255/hostaway-mcp/`
2. Edit `.env` file
3. Add these lines at the bottom:

```bash
# Supabase Configuration (for API Key validation)
SUPABASE_URL=https://iixikajovibmfvinkwex.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlpeGlrYWpvdmlibWZ2aW5rd2V4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNjg3MDY5NCwiZXhwIjoyMDUyNDQ2Njk0fQ.VCcTWbWE-3Hfi5UaNz4A4yEqqqJdEd3l4sEfhKBBHIg
```

4. Save the file

## Step 4: Install Dependencies (Terminal in cPanel)

Hostinger usually has **Terminal** app in cPanel:
1. Open Terminal from Hostinger control panel
2. Run these commands:

```bash
cd /home/u631126255/hostaway-mcp

# Install supabase dependency
pip3 install --user supabase-py

# Or if pip3 doesn't work:
python3 -m pip install --user supabase-py
```

## Step 5: Restart the Service

In Terminal, run:

```bash
# Stop existing server
pkill -f "uvicorn.*main:app" || true
pkill -f "python.*mcp" || true
sleep 2

# Start new server
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080 > /tmp/mcp-server.log 2>&1 &

# Check if it started
sleep 5
ps aux | grep uvicorn

# Test health
curl http://localhost:8080/health

# Test with API key
curl -H "X-API-Key: mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk" http://localhost:8080/health
```

## Alternative: If Terminal Not Available

If Hostinger doesn't provide Terminal access:

1. **Enable SSH in cPanel**:
   - Go to **Advanced → SSH Access**
   - Enable SSH
   - Generate/add your SSH public key

2. **Generate SSH key locally** (if you don't have one):
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub  # Copy this
```

3. **Add key to Hostinger**:
   - Paste your public key in cPanel SSH settings
   - Try SSH again: `ssh u631126255@72.60.233.157`

## Verification

After restart, test from your local machine:

```bash
# Health check
curl http://72.60.233.157:8080/health

# With API key
curl -H "X-API-Key: mcp_Quyj29roULrQZc3ICrGmUcP31Px8Ntk" \
     http://72.60.233.157:8080/health
```

Then restart Claude Desktop and test the MCP connection.
