# Hostaway MCP Server - Quickstart Guide

Get the Hostaway MCP Server running in under 10 minutes. This guide walks you through installation, configuration, and your first MCP tool invocation.

---

## Overview

The Hostaway MCP Server exposes Hostaway property management operations as AI-callable tools using the Model Context Protocol (MCP). Built with FastAPI-MCP, it enables AI assistants like Claude to manage listings, bookings, and guest communications.

**What you'll accomplish:**
- Install the server and dependencies
- Configure Hostaway API credentials
- Start the MCP server
- Make your first tool call
- Verify everything works

**Time to complete:** 10 minutes

---

## Prerequisites

Before you begin, ensure you have:

### Required Software

- **Python 3.12 or higher**
  ```bash
  # Check your Python version
  python3 --version
  # Output should be: Python 3.12.x or higher
  ```

- **uv package manager** (recommended) or pip
  ```bash
  # Install uv (if not installed)
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Verify installation
  uv --version
  ```

- **Git** (for cloning the repository)
  ```bash
  git --version
  ```

### Required Credentials

- **Hostaway API Key**: Get from [Hostaway Dashboard](https://dashboard.hostaway.com/) → Settings → API
- **Hostaway Account ID**: Found in Hostaway Dashboard URL or API settings

### Recommended (Optional)

- **Claude Desktop** or another MCP client for testing
- **Docker** (for containerized deployment)
- **HTTPie or curl** (for API testing)

---

## Installation

### Step 1: Clone the Repository

```bash
# Navigate to your projects directory
cd ~/AI_Projects  # Or your preferred location

# Clone the repository
git clone <repository-url> hostaway-mcp
cd hostaway-mcp
```

**Expected output:**
```
Cloning into 'hostaway-mcp'...
remote: Enumerating objects: 45, done.
remote: Counting objects: 100% (45/45), done.
```

### Step 2: Create Virtual Environment

```bash
# Create Python virtual environment
python3.12 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

**Expected output:**
```
(.venv) user@machine:~/AI_Projects/hostaway-mcp$
```

Your prompt should now show `(.venv)` indicating the virtual environment is active.

### Step 3: Install Dependencies

#### Using uv (Recommended)

```bash
# Install core dependencies
uv add fastapi fastapi-mcp uvicorn httpx pydantic-settings

# Install development dependencies
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy

# Verify installation
uv pip list | grep fastapi-mcp
```

#### Using pip

```bash
# Install core dependencies
pip install fastapi fastapi-mcp uvicorn httpx pydantic-settings

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov ruff mypy

# Verify installation
pip show fastapi-mcp
```

**Expected output:**
```
Name: fastapi-mcp
Version: 0.x.x
Summary: FastAPI integration for Model Context Protocol
```

---

## Configuration

### Step 1: Create Environment File

Create a `.env` file in the project root with your configuration:

```bash
# Create .env file
cat > .env << 'EOF'
# Hostaway API Configuration
MCP_HOSTAWAY_API_KEY=your_hostaway_api_key_here
MCP_HOSTAWAY_ACCOUNT_ID=your_account_id_here
MCP_HOSTAWAY_BASE_URL=https://api.hostaway.com/v1

# MCP Server Configuration
MCP_SERVER_NAME=hostaway-mcp
MCP_SERVER_VERSION=0.1.0

# Authentication
MCP_ENABLE_AUTH=true
MCP_API_KEY_HEADER=X-API-Key
MCP_ALLOWED_API_KEYS=["dev-key-123","test-key-456"]

# Development Settings
MCP_USE_HTTP_TRANSPORT=true
MCP_RATE_LIMIT_ENABLED=true
MCP_RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
EOF
```

### Step 2: Update Configuration

Edit `.env` with your actual credentials:

```bash
# Open in your preferred editor
nano .env
# or
vim .env
# or
code .env
```

**Replace these values:**
- `your_hostaway_api_key_here` → Your actual Hostaway API key
- `your_account_id_here` → Your Hostaway account ID
- Update `MCP_ALLOWED_API_KEYS` with your own keys (keep them secret!)

**Configuration explained:**

| Variable | Purpose | Example |
|----------|---------|---------|
| `MCP_HOSTAWAY_API_KEY` | Hostaway API authentication | `ha_abc123xyz...` |
| `MCP_HOSTAWAY_ACCOUNT_ID` | Your Hostaway account | `12345` |
| `MCP_ENABLE_AUTH` | Require API keys for MCP tools | `true` (production), `false` (development) |
| `MCP_ALLOWED_API_KEYS` | Valid API keys (JSON array) | `["key1","key2"]` |
| `MCP_USE_HTTP_TRANSPORT` | Enable HTTP endpoints for testing | `true` (development), `false` (production) |
| `MCP_RATE_LIMIT_PER_MINUTE` | Max requests per minute per key | `60` |

### Step 3: Verify Configuration

```bash
# Check .env file is created and has correct permissions
ls -la .env

# Verify .env is in .gitignore (security!)
grep ".env" .gitignore
```

**Expected output:**
```
-rw------- 1 user user 542 Oct 12 10:30 .env
.env
```

The `.env` file should have restricted permissions (600) and be in `.gitignore`.

### Step 4: Set Rate Limits (Optional)

For production, adjust rate limits based on your needs:

```bash
# Conservative (for testing)
MCP_RATE_LIMIT_PER_MINUTE=10

# Moderate (for development)
MCP_RATE_LIMIT_PER_MINUTE=60

# Generous (for production with monitoring)
MCP_RATE_LIMIT_PER_MINUTE=300
```

---

## Running the Server

### Development Mode (Hot Reload)

Start the server with automatic reload on code changes:

```bash
# Start server with uvicorn
uvicorn src.mcp.server:mcp_app --reload --port 8000 --host 0.0.0.0
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/hostaway-mcp']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

The server is now running at `http://localhost:8000`.

### Production Mode (Gunicorn)

For production, use Gunicorn with multiple workers:

```bash
# Install gunicorn if not already installed
pip install gunicorn

# Start with 4 worker processes
gunicorn src.mcp.server:mcp_app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

**Expected output:**
```
[2025-10-12 10:35:00] [12345] [INFO] Starting gunicorn 21.2.0
[2025-10-12 10:35:00] [12345] [INFO] Listening at: http://0.0.0.0:8000 (12345)
[2025-10-12 10:35:00] [12345] [INFO] Using worker: uvicorn.workers.UvicornWorker
[2025-10-12 10:35:00] [12346] [INFO] Booting worker with pid: 12346
[2025-10-12 10:35:00] [12347] [INFO] Booting worker with pid: 12347
[2025-10-12 10:35:00] [12348] [INFO] Booting worker with pid: 12348
[2025-10-12 10:35:00] [12349] [INFO] Booting worker with pid: 12349
```

### Docker Deployment

Run using Docker for isolated deployment:

```bash
# Build Docker image
docker build -t hostaway-mcp:latest .

# Run container
docker run -d \
  --name hostaway-mcp \
  -p 8000:8000 \
  --env-file .env \
  hostaway-mcp:latest

# Check logs
docker logs -f hostaway-mcp
```

**Using Docker Compose:**

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Health Check Verification

Verify the server is running correctly:

```bash
# Using curl
curl http://localhost:8000/health

# Using httpie
http GET http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "hostaway-mcp",
  "version": "0.1.0",
  "timestamp": "2025-10-12T10:35:00.000Z"
}
```

**Status codes:**
- `200 OK` → Server is healthy
- `503 Service Unavailable` → Server has issues

---

## First MCP Tool Invocation

Now let's make your first tool call to the MCP server.

### Step 1: Authentication Flow

The server requires API key authentication. Include your key in the `X-API-Key` header.

```bash
# Test authentication (should succeed)
curl -X GET http://localhost:8000/api/v1/listings/123 \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json"

# Test without authentication (should fail)
curl -X GET http://localhost:8000/api/v1/listings/123
```

**Expected output (authenticated):**
```json
{
  "listing": {
    "id": 123,
    "name": "Beautiful Beach House",
    "address": "123 Ocean Drive",
    "city": "Miami",
    "max_guests": 6,
    "bedrooms": 3,
    "bathrooms": 2,
    "property_type": "house"
  },
  "success": true,
  "message": "Listing retrieved successfully"
}
```

**Expected output (unauthenticated):**
```json
{
  "detail": "API key required"
}
```

### Step 2: List Properties Example

Retrieve a specific property listing:

```bash
# Using curl
curl -X GET "http://localhost:8000/api/v1/listings/12345" \
  -H "X-API-Key: dev-key-123" \
  -H "Accept: application/json"

# Using httpie (cleaner syntax)
http GET http://localhost:8000/api/v1/listings/12345 \
  X-API-Key:dev-key-123
```

**Expected response:**
```json
{
  "listing": {
    "id": 12345,
    "name": "Luxury Downtown Apartment",
    "address": "456 Main Street, Apt 5B",
    "city": "San Francisco",
    "max_guests": 4,
    "bedrooms": 2,
    "bathrooms": 2,
    "property_type": "apartment"
  },
  "success": true,
  "message": "Listing retrieved successfully"
}
```

### Step 3: Search Bookings Example

Search for bookings with filters:

```bash
# Search bookings by date range and status
curl -X POST "http://localhost:8000/api/v1/bookings/search" \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "check_in_from": "2025-11-01",
      "check_in_to": "2025-11-30",
      "status": "confirmed"
    },
    "page": 1,
    "page_size": 10
  }'
```

**Expected response:**
```json
{
  "bookings": [
    {
      "id": 789,
      "listing_id": 12345,
      "guest_name": "John Doe",
      "check_in": "2025-11-15",
      "check_out": "2025-11-20",
      "status": "confirmed",
      "total_price": 850.00,
      "num_guests": 2
    },
    {
      "id": 790,
      "listing_id": 12346,
      "guest_name": "Jane Smith",
      "check_in": "2025-11-22",
      "check_out": "2025-11-25",
      "status": "confirmed",
      "total_price": 450.00,
      "num_guests": 1
    }
  ],
  "total_count": 2,
  "page": 1,
  "page_size": 10,
  "success": true
}
```

### Step 4: Error Handling Demonstration

Test error responses:

**Invalid listing ID:**
```bash
curl -X GET "http://localhost:8000/api/v1/listings/99999" \
  -H "X-API-Key: dev-key-123"
```

**Expected response:**
```json
{
  "success": false,
  "error": {
    "code": "HTTP_404",
    "message": "Listing not found: Resource with ID 99999 does not exist"
  },
  "timestamp": "2025-10-12T10:40:00.000Z"
}
```

**Invalid API key:**
```bash
curl -X GET "http://localhost:8000/api/v1/listings/123" \
  -H "X-API-Key: invalid-key"
```

**Expected response:**
```json
{
  "detail": "Invalid API key"
}
```

**Rate limit exceeded:**
```bash
# Make 61 requests rapidly (exceeds 60/minute limit)
for i in {1..61}; do
  curl -X GET "http://localhost:8000/api/v1/listings/123" \
    -H "X-API-Key: dev-key-123"
done
```

**Expected response (on 61st request):**
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

### Step 5: Using MCP Client (Claude Desktop)

If you have Claude Desktop installed:

1. **Add server to Claude Desktop config:**

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hostaway": {
      "command": "uvicorn",
      "args": [
        "src.mcp.server:mcp_app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "env": {
        "MCP_HOSTAWAY_API_KEY": "your_key_here",
        "MCP_HOSTAWAY_ACCOUNT_ID": "your_account_here"
      }
    }
  }
}
```

2. **Restart Claude Desktop**

3. **Test tool discovery:**

In Claude, type:
```
What tools do you have available from the Hostaway server?
```

Claude should list:
- `get_listing`
- `search_bookings`
- `send_guest_message`
- (other available tools)

4. **Invoke a tool:**

```
Can you get details for listing ID 12345?
```

Claude will use the `get_listing` tool and return the property details.

---

## Testing

Verify everything works with the test suite.

### Run Unit Tests

```bash
# Run all unit tests
pytest tests/unit -v

# Run specific test file
pytest tests/unit/test_listings.py -v

# Run with coverage
pytest tests/unit --cov=src --cov-report=html
```

**Expected output:**
```
tests/unit/test_listings.py::test_get_listing_success PASSED        [ 25%]
tests/unit/test_listings.py::test_get_listing_not_found PASSED     [ 50%]
tests/unit/test_listings.py::test_get_listing_unauthorized PASSED  [ 75%]
tests/unit/test_bookings.py::test_search_bookings_success PASSED   [100%]

======================== 4 passed in 2.34s =========================
```

### Run Integration Tests

```bash
# Start test server first
pytest tests/integration -v

# Run specific integration test
pytest tests/integration/test_mcp_integration.py -v
```

**Expected output:**
```
tests/integration/test_mcp_integration.py::test_mcp_tool_discovery PASSED     [ 50%]
tests/integration/test_mcp_integration.py::test_mcp_tool_invocation PASSED    [100%]

======================== 2 passed in 5.67s =========================
```

### Run MCP Protocol Tests

```bash
# Test MCP protocol compliance
pytest tests/mcp -v --mcp-protocol
```

### Generate Coverage Report

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=term --cov-report=html tests/

# Open HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**Expected coverage:**
```
Name                          Stmts   Miss  Cover
-------------------------------------------------
src/api/main.py                  45      2    96%
src/mcp/server.py                32      1    97%
src/mcp/config.py                28      0   100%
src/mcp/auth.py                  40      3    93%
src/api/routes/listings.py       56      4    93%
src/api/routes/bookings.py       72      6    92%
-------------------------------------------------
TOTAL                           273     16    94%
```

---

## Troubleshooting

Common issues and solutions.

### Authentication Errors

**Problem:** "API key required" error

**Solutions:**
```bash
# 1. Verify .env file exists and has correct values
cat .env | grep MCP_ALLOWED_API_KEYS

# 2. Check API key format (must be JSON array)
MCP_ALLOWED_API_KEYS=["key1","key2"]  # Correct
MCP_ALLOWED_API_KEYS=key1,key2         # Wrong

# 3. Disable auth for testing
# In .env:
MCP_ENABLE_AUTH=false

# 4. Verify header name matches
curl -v http://localhost:8000/api/v1/listings/123 \
  -H "X-API-Key: dev-key-123"  # Default header name
```

### Rate Limit Problems

**Problem:** "Rate limit exceeded" errors

**Solutions:**
```bash
# 1. Increase rate limit (for development)
# In .env:
MCP_RATE_LIMIT_PER_MINUTE=300

# 2. Disable rate limiting (testing only)
MCP_RATE_LIMIT_ENABLED=false

# 3. Wait 60 seconds for rate limit to reset

# 4. Check rate limit status
curl http://localhost:8000/api/v1/rate-limit-status \
  -H "X-API-Key: dev-key-123"
```

### Connection Issues

**Problem:** "Connection refused" or server not responding

**Solutions:**
```bash
# 1. Verify server is running
ps aux | grep uvicorn

# 2. Check port is not in use
lsof -i :8000

# 3. Check firewall settings
sudo ufw status  # Linux
# Allow port 8000 if blocked

# 4. Verify correct host/port
netstat -an | grep 8000

# 5. Check server logs
tail -f logs/server.log
```

### Hostaway API Errors

**Problem:** "Hostaway API error" or 401/403 from Hostaway

**Solutions:**
```bash
# 1. Verify Hostaway credentials
# Test directly with Hostaway API:
curl https://api.hostaway.com/v1/listings \
  -H "Authorization: Bearer YOUR_HOSTAWAY_KEY"

# 2. Check API key format
# In .env:
MCP_HOSTAWAY_API_KEY=Bearer_abc123...  # If Hostaway uses Bearer
# or
MCP_HOSTAWAY_API_KEY=abc123...         # If just the key

# 3. Verify account ID is correct
# Check Hostaway dashboard URL:
# https://dashboard.hostaway.com/account/12345
#                                        ^^^^^ This is your account ID

# 4. Check API rate limits on Hostaway side
# Wait if you've exceeded Hostaway's limits
```

### Import Errors

**Problem:** "ModuleNotFoundError" or import errors

**Solutions:**
```bash
# 1. Verify virtual environment is activated
which python  # Should show .venv path

# 2. Reinstall dependencies
pip install -r requirements.txt
# or
uv sync

# 3. Check Python version
python --version  # Should be 3.12+

# 4. Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Database/Migration Errors

**Problem:** If using database for caching

**Solutions:**
```bash
# 1. Run migrations
alembic upgrade head

# 2. Reset database (development only!)
alembic downgrade base
alembic upgrade head

# 3. Check database connection
# Verify DATABASE_URL in .env is correct
```

---

## Next Steps

Congratulations! Your Hostaway MCP Server is running. Here's what to do next:

### 1. Explore Available Tools

View all available MCP tools:

```bash
# List all endpoints (these become MCP tools)
curl http://localhost:8000/docs
# Opens OpenAPI documentation
```

**Available tools:**
- Listings: get, list, check availability
- Bookings: search, create, update, get details
- Guests: send messages, get history

### 2. Read Full Documentation

Dive deeper into specific topics:

- **[FastAPI-MCP Integration Guide](/Users/darrenmorgan/AI_Projects/hostaway-mcp/docs/FASTAPI_MCP_GUIDE.md)**
  - Authentication strategies
  - Performance optimization
  - Error handling patterns

- **[Implementation Roadmap](/Users/darrenmorgan/AI_Projects/hostaway-mcp/docs/IMPLEMENTATION_ROADMAP.md)**
  - Complete feature list
  - Development phases
  - Architecture decisions

- **[API Reference](/Users/darrenmorgan/AI_Projects/hostaway-mcp/docs/API_REFERENCE.md)** (coming soon)
  - Detailed endpoint documentation
  - Request/response schemas
  - Code examples

### 3. Advanced Configuration

Customize the server for your needs:

**Rate Limiting:**
```python
# src/mcp/config.py
rate_limit_per_minute: int = 300  # Increase for production
rate_limit_burst: int = 10         # Allow bursts
```

**Logging:**
```python
# Add structured logging
LOG_LEVEL=DEBUG  # Development
LOG_LEVEL=INFO   # Production
LOG_FORMAT=json  # For log aggregation
```

**Caching:**
```python
# Enable response caching
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300
CACHE_BACKEND=redis  # or memory
```

### 4. Integrate with Your Workflow

**Connect to Claude Desktop:**
- Follow Step 5 in "First MCP Tool Invocation" section
- Test with real property management tasks

**Build Custom MCP Client:**
- Use MCP SDK for Python: `pip install mcp`
- See examples in `examples/custom_client.py`

**Deploy to Production:**
- Use Docker Compose for easy deployment
- Set up monitoring (Prometheus, Grafana)
- Configure SSL/TLS certificates
- Set up log aggregation (ELK stack, CloudWatch)

### 5. Contribute to Development

Help improve the project:

```bash
# Create a feature branch
git checkout -b feature/new-tool

# Make changes and test
pytest tests/ --cov=src

# Commit using conventional commits
git commit -m "feat: Add calendar sync tool"

# Push and create pull request
git push origin feature/new-tool
```

**Development workflow:**
1. Use spec-kit commands (`/speckit.specify`, `/speckit.plan`, etc.)
2. Write tests first (TDD)
3. Implement features
4. Update documentation
5. Submit PR

---

## Resources

### Documentation

- **Project Documentation:** `/Users/darrenmorgan/AI_Projects/hostaway-mcp/docs/`
- **FastAPI-MCP Guide:** `docs/FASTAPI_MCP_GUIDE.md`
- **Implementation Roadmap:** `docs/IMPLEMENTATION_ROADMAP.md`

### External Resources

- **FastAPI-MCP**: https://fastapi-mcp.tadata.com/
- **MCP Specification**: https://modelcontextprotocol.io/
- **Hostaway API**: https://docs.hostaway.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/

### Community

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Spec-Kit**: Learn about spec-driven development

### Support

Need help?

1. **Check documentation** in `docs/` folder
2. **Review troubleshooting** section above
3. **Search existing issues** on GitHub
4. **Ask in discussions** for general questions
5. **Open an issue** for bugs or feature requests

---

## Summary

You've successfully:

- ✅ Installed Python 3.12+ and uv package manager
- ✅ Cloned and set up the project
- ✅ Configured Hostaway API credentials
- ✅ Started the MCP server
- ✅ Made your first authenticated tool call
- ✅ Tested listings and bookings endpoints
- ✅ Verified health checks and error handling
- ✅ Run the test suite

**Your server is now ready for:**
- Integration with Claude Desktop
- Building custom MCP clients
- Development of additional tools
- Production deployment

**Next steps:**
- Explore the [FastAPI-MCP Guide](docs/FASTAPI_MCP_GUIDE.md) for advanced features
- Review the [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md) for future features
- Start building your own MCP tools

---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-12
**Tested On:** macOS (Darwin 24.6.0), Python 3.12
**Status:** Production Ready ✅

---

## Quick Reference Card

### Common Commands

```bash
# Start server (development)
uvicorn src.mcp.server:mcp_app --reload

# Start server (production)
gunicorn src.mcp.server:mcp_app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Run tests
pytest tests/ -v --cov=src

# Check health
curl http://localhost:8000/health

# Test authentication
curl http://localhost:8000/api/v1/listings/123 -H "X-API-Key: dev-key-123"

# View API docs
open http://localhost:8000/docs
```

### Configuration Quick Reference

| Setting | Development | Production |
|---------|-------------|------------|
| `MCP_ENABLE_AUTH` | `false` | `true` |
| `MCP_USE_HTTP_TRANSPORT` | `true` | `false` |
| `MCP_RATE_LIMIT_PER_MINUTE` | `60` | `300` |
| `LOG_LEVEL` | `DEBUG` | `INFO` |

### Troubleshooting Checklist

- [ ] Virtual environment activated?
- [ ] Dependencies installed?
- [ ] `.env` file configured?
- [ ] Hostaway credentials valid?
- [ ] Server running on correct port?
- [ ] Firewall allows connections?
- [ ] API key in correct format?
- [ ] Rate limits not exceeded?

### Support Contacts

- **Documentation**: `/Users/darrenmorgan/AI_Projects/hostaway-mcp/docs/`
- **GitHub Issues**: `<repository-url>/issues`
- **Spec-Kit**: `.claude/commands/`

---

**Happy building! 🚀**
