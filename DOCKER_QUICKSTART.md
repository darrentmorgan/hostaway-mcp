# Docker Quick Start Guide

## Prerequisites

- Docker Desktop installed and running
- Hostaway API credentials (Account ID and Secret Key)

## Method 1: Docker Compose (Recommended)

### 1. Verify Configuration

Check that your `.env` file has the correct credentials:

```bash
cat .env
```

Should contain:
```bash
HOSTAWAY_ACCOUNT_ID=your_account_id
HOSTAWAY_SECRET_KEY=your_secret_key
```

### 2. Build and Start

```bash
# Build and start in detached mode
docker compose up -d --build

# View logs
docker compose logs -f hostaway-mcp
```

### 3. Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Test a real endpoint
curl http://localhost:8000/api/listings?limit=3
```

### 4. Stop/Restart

```bash
# Stop
docker compose down

# Restart
docker compose restart

# View container status
docker compose ps
```

## Method 2: Docker Standalone

### 1. Build Image

```bash
docker build -t hostaway-mcp:latest .
```

### 2. Run Container

```bash
docker run -d \
  --name hostaway-mcp \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  hostaway-mcp:latest
```

### 3. View Logs

```bash
docker logs -f hostaway-mcp
```

### 4. Stop Container

```bash
docker stop hostaway-mcp
docker rm hostaway-mcp
```

## Troubleshooting

### Issue: Container exits immediately

**Check logs:**
```bash
docker compose logs hostaway-mcp
```

**Common causes:**
1. Missing environment variables → Check `.env` file
2. Invalid credentials → Verify Hostaway API credentials
3. Port conflict → Kill process on port 8000: `lsof -ti :8000 | xargs kill -9`

### Issue: Health check failing

**Test health endpoint manually:**
```bash
docker exec hostaway-mcp-server curl http://localhost:8000/health
```

### Issue: Can't access from browser

**Check if container is running:**
```bash
docker ps | grep hostaway-mcp
```

**Check port mapping:**
```bash
docker port hostaway-mcp-server
```

Should show: `8000/tcp -> 0.0.0.0:8000`

## Production-Like Setup (with Nginx)

Uncomment the nginx service in `docker-compose.yml` for a production-like setup with reverse proxy:

```bash
# Edit docker-compose.yml (uncomment nginx section)
# Then start both services
docker compose up -d
```

This will expose:
- Port 80 (HTTP) → routed to MCP server
- Port 443 (HTTPS) → requires SSL certificates

## Performance Tips

1. **Use volumes for logs:**
   - Logs are automatically mounted to `./logs/` directory
   - Check them with: `tail -f logs/app.log | jq`

2. **Monitor resource usage:**
   ```bash
   docker stats hostaway-mcp-server
   ```

3. **Restart on configuration change:**
   ```bash
   docker-compose restart
   ```

## Next Steps

1. ✅ Verify all endpoints work: http://localhost:8000/docs
2. ✅ Test MCP tool discovery (if using Claude Desktop)
3. ✅ Check logs for any errors: `docker-compose logs -f`
4. 🚀 Deploy to production using the same Docker image

## Recommended Workflow

```bash
# 1. Start services
docker compose up -d

# 2. Tail logs in one terminal
docker compose logs -f

# 3. Test in another terminal
curl http://localhost:8000/health

# 4. When done
docker compose down
```
