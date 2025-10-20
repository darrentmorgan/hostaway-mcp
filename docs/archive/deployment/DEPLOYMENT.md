# Deployment Guide - Hostaway MCP Server

This guide covers automated deployment to your Hostinger VPS server.

## 🚀 Quick Deploy (Manual)

```bash
./scripts/deploy.sh production
```

## 📋 Prerequisites

### 1. SSH Access Setup

First, set up SSH key-based authentication to your server:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "deployment@hostaway-mcp"

# Copy your public key to the server
ssh-copy-id -p 22 root@72.60.233.157

# Test connection
ssh root@72.60.233.157 "echo 'SSH works!'"
```

### 2. Server Setup (One-time)

On your Hostinger VPS, ensure the following:

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create deployment directory
mkdir -p /var/www/hostaway-mcp
chown -R $USER:$USER /var/www/hostaway-mcp

# Create systemd service (if not exists)
sudo nano /etc/systemd/system/hostaway-mcp.service
```

**Systemd service file** (`/etc/systemd/system/hostaway-mcp.service`):

```ini
[Unit]
Description=Hostaway MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/hostaway-mcp
Environment="PATH=/root/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/root/.local/bin/uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hostaway-mcp
sudo systemctl start hostaway-mcp
sudo systemctl status hostaway-mcp
```

### 3. Environment Variables on Server

Create `.env` file on the server at `/var/www/hostaway-mcp/.env`:

```bash
ssh root@72.60.233.157
cd /var/www/hostaway-mcp
nano .env
```

Add your production environment variables (DO NOT commit these):

```env
# Supabase Production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_production_service_key
SUPABASE_ANON_KEY=your_production_anon_key

# Stripe Production
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_LISTING_PRICE_ID=price_xxx

# Hostaway (if needed for testing)
HOSTAWAY_ACCOUNT_ID=161051
HOSTAWAY_SECRET_KEY=your_secret_key
HOSTAWAY_API_BASE_URL=https://api.hostaway.com/v1

# Production settings
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## 🤖 Automated Deployment (GitHub Actions)

### Setup GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `SSH_PRIVATE_KEY` | `[your private key]` | Contents of ~/.ssh/id_ed25519 |
| `SERVER_IP` | `72.60.233.157` | Your VPS IP |
| `SERVER_USER` | `root` | SSH user |
| `SERVER_PORT` | `22` | SSH port |
| `DEPLOY_PATH` | `/var/www/hostaway-mcp` | Deployment directory |
| `SERVICE_NAME` | `hostaway-mcp` | Systemd service name |

### Get Your SSH Private Key

```bash
cat ~/.ssh/id_ed25519
```

Copy the entire output (including `-----BEGIN` and `-----END` lines) and paste into the `SSH_PRIVATE_KEY` secret.

### Trigger Deployment

**Automatic**: Push to `main` or `production` branch
```bash
git add .
git commit -m "feat: update feature"
git push origin main
```

**Manual**: Go to GitHub Actions tab → "Deploy to Hostinger VPS" → "Run workflow"

---

## 🔧 Manual Deployment Options

### Option 1: Using the deploy script

```bash
# Deploy to production
./scripts/deploy.sh production

# With custom server
DEPLOY_SERVER_IP=72.60.233.157 DEPLOY_USER=root ./scripts/deploy.sh
```

### Option 2: Direct rsync

```bash
rsync -avz --delete \
  --exclude '.git' \
  --exclude '.env' \
  --exclude '__pycache__' \
  --exclude '.venv' \
  ./ root@72.60.233.157:/var/www/hostaway-mcp/

ssh root@72.60.233.157 "cd /var/www/hostaway-mcp && sudo systemctl restart hostaway-mcp"
```

---

## 🔍 Troubleshooting

### Check server logs

```bash
ssh root@72.60.233.157
sudo journalctl -u hostaway-mcp -f  # Follow logs in real-time
sudo systemctl status hostaway-mcp  # Check service status
```

### Test deployment

```bash
# Health check
curl http://72.60.233.157:8080/health

# API test
curl http://72.60.233.157:8080/
```

### Restart service manually

```bash
ssh root@72.60.233.157
sudo systemctl restart hostaway-mcp
sudo systemctl status hostaway-mcp
```

### Check Python version

```bash
ssh root@72.60.233.157
python3 --version  # Should be 3.12+
uv --version
```

---

## 📝 Deployment Checklist

Before deploying to production:

- [ ] Update `.env` on server with production credentials
- [ ] Test deployment with staging branch first
- [ ] Verify all environment variables are set
- [ ] Check systemd service is running
- [ ] Test health endpoint: `curl http://72.60.233.157:8080/health`
- [ ] Monitor logs for errors: `journalctl -u hostaway-mcp -f`
- [ ] Verify Supabase connection works
- [ ] Test Stripe webhooks (if configured)

---

## 🔐 Security Notes

1. **Never commit `.env` files** - They're in .gitignore
2. **Use different credentials** for production vs development
3. **Rotate SSH keys** regularly
4. **Keep service role keys** secret (never in frontend)
5. **Use HTTPS** in production (setup nginx/caddy reverse proxy)
6. **Enable firewall** on VPS (ufw allow 22,80,443,8080)

---

## 🚀 Next Steps

1. Set up nginx reverse proxy for HTTPS
2. Configure domain name (hostaway-mcp.your-domain.com)
3. Set up monitoring (Sentry, Datadog, etc.)
4. Configure automated backups (Supabase + code)
5. Set up staging environment

---

**Deployment Status**:
- Script: `./scripts/deploy.sh` ✅
- GitHub Actions: `.github/workflows/deploy.yml` ✅
- Manual rsync: Available ✅
