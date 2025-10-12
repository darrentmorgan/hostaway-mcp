# Hostaway MCP Server

A FastAPI-based Model Context Protocol (MCP) server that exposes Hostaway property management operations as AI-callable tools.

## Overview

This project enables AI assistants like Claude to interact with Hostaway's property management platform through standardized MCP tools. Built with FastAPI-MCP, it provides type-safe, authenticated access to listings, bookings, and guest communication.

## Features

- **MCP Protocol Support**: Expose Hostaway API as AI-callable tools
- **Type Safety**: Full Pydantic model validation
- **Authentication**: Secure API key and OAuth2 support
- **Async Performance**: ASGI transport for efficient communication
- **Spec-Driven Development**: Integrated with Spec-Kit workflow

## Quick Start

### Prerequisites

- Python 3.12+
- uv or pip package manager
- Hostaway API credentials

### Installation

```bash
# Clone repository
git clone <repository-url>
cd hostaway-mcp

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
uv add fastapi fastapi-mcp uvicorn httpx pydantic-settings

# Configure environment
cp .env.example .env
# Edit .env with your Hostaway credentials
```

### Running the Server

```bash
# Development mode
uvicorn src.mcp.server:mcp_app --reload

# Production mode
gunicorn src.mcp.server:mcp_app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## Documentation

### Core Documentation

- **[FastAPI-MCP Integration Guide](docs/FASTAPI_MCP_GUIDE.md)** - Complete guide to using FastAPI-MCP
  - Installation and setup
  - Core concepts and architecture
  - Implementation examples
  - Authentication strategies
  - Deployment options
  - Best practices and troubleshooting

- **[Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)** - Project implementation plan
  - Phase-by-phase development strategy
  - Sprint timeline and milestones
  - Project structure and organization
  - Risk mitigation
  - Success criteria

### Spec-Kit Workflow

This project uses Spec-Kit for spec-driven development:

1. **Define Constitution**: `/speckit.constitution`
2. **Create Specification**: `/speckit.specify`
3. **Generate Plan**: `/speckit.plan`
4. **Create Tasks**: `/speckit.tasks`
5. **Implement**: `/speckit.implement`

## Project Structure

```
hostaway-mcp/
├── .claude/              # Spec-kit commands
├── .specify/             # Spec-kit templates
├── src/
│   ├── api/             # FastAPI application
│   │   ├── main.py      # Main app
│   │   └── routes/      # API endpoints
│   ├── mcp/             # MCP server
│   │   ├── server.py    # MCP setup
│   │   ├── config.py    # Configuration
│   │   └── auth.py      # Authentication
│   ├── services/        # Business logic
│   └── models/          # Pydantic models
├── tests/               # Test suite
├── docs/                # Documentation
└── .env                 # Environment config
```

## Available Tools (Planned)

### Listings
- `get_listing` - Retrieve listing details
- `list_listings` - List all listings
- `check_availability` - Check date availability

### Bookings
- `search_bookings` - Search with filters
- `get_booking` - Get booking details
- `create_booking` - Create new booking

### Guests
- `send_guest_message` - Send message to guest
- `get_guest` - Get guest details
- `get_message_history` - View communication history

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# All tests with coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Linting
ruff check src/

# Type checking
mypy src/

# Formatting
ruff format src/
```

## Deployment

### Docker

```bash
# Build image
docker build -t hostaway-mcp .

# Run container
docker run -p 8000:8000 --env-file .env hostaway-mcp
```

### Docker Compose

```bash
docker-compose up -d
```

## Security

- API keys stored in environment variables
- Input validation with Pydantic
- Rate limiting enabled
- Audit logging for all tool calls
- HTTPS required in production

## Contributing

1. Follow spec-driven development workflow
2. Write tests for all new features
3. Maintain >80% code coverage
4. Update documentation
5. Follow security best practices

## License

MIT

## Resources

- [FastAPI-MCP Repository](https://github.com/tadata-org/fastapi_mcp)
- [FastAPI-MCP Documentation](https://fastapi-mcp.tadata.com/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Hostaway API Docs](https://docs.hostaway.com/)
- [Spec-Kit](https://github.com/github/spec-kit)

## Support

For issues and questions:
- Check [Documentation](docs/)
- Review [Troubleshooting Guide](docs/FASTAPI_MCP_GUIDE.md#troubleshooting)
- Open an issue on GitHub

---

**Status**: Initial Setup Complete ✅
**Next Step**: Begin Phase 1 - Environment Setup (see [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md))
