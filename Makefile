.PHONY: help pre-push format lint typecheck test test-integration test-unit clean install

# Default target
help:
	@echo "Available targets:"
	@echo "  pre-push          - Run all pre-push validation checks (format, lint, typecheck, tests)"
	@echo "  format            - Run ruff format on codebase"
	@echo "  format-check      - Check if code is formatted correctly"
	@echo "  lint              - Run ruff linter"
	@echo "  typecheck         - Run mypy type checker"
	@echo "  test              - Run all tests with coverage"
	@echo "  test-integration  - Run integration tests only"
	@echo "  test-unit         - Run unit tests only"
	@echo "  clean             - Remove build artifacts and cache"
	@echo "  install           - Install dependencies with uv"

# Pre-push validation (run before pushing to CI/CD)
pre-push:
	@./scripts/pre-push-check.sh

# Formatting
format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

# Linting
lint:
	uv run ruff check .

# Type checking
typecheck:
	uv run mypy src/ --ignore-missing-imports

# Testing
test:
	uv run pytest --cov=src --cov-report=term-missing

test-integration:
	uv run pytest tests/integration/ -v

test-unit:
	uv run pytest tests/unit/ -v

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage coverage.xml

# Install dependencies
install:
	uv sync
