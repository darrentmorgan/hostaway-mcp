"""Unit tests for ConfigService.

Tests configuration loading, hot-reload, file watching, and endpoint overrides.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.models.token_budget import EndpointBudgetOverride, TokenBudgetConfig
from src.services.config_service import ConfigService, get_config_service


class TestConfigService:
    """Test suite for ConfigService."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        service = ConfigService(config_path="/nonexistent/path.yaml", auto_reload=False)

        assert service.config.output_token_threshold == 4000
        assert service.config.hard_output_token_cap == 12000
        assert service.config.default_page_size == 50
        assert service.config.max_page_size == 200
        assert service.config.enable_summarization is True
        assert service.config.enable_pagination is True
        assert service.endpoint_overrides == {}

    def test_load_config_from_yaml(self, tmp_path):
        """Test loading configuration from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "context_protection": {
                "output_token_threshold": 5000,
                "hard_output_token_cap": 15000,
                "default_page_size": 100,
                "max_page_size": 500,
                "enable_summarization": False,
                "enable_pagination": True,
            }
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        service = ConfigService(config_path=config_file, auto_reload=False)

        assert service.config.output_token_threshold == 5000
        assert service.config.hard_output_token_cap == 15000
        assert service.config.default_page_size == 100
        assert service.config.max_page_size == 500
        assert service.config.enable_summarization is False
        assert service.config.enable_pagination is True

    def test_load_config_with_endpoint_overrides(self, tmp_path):
        """Test loading endpoint-specific overrides."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "context_protection": {
                "output_token_threshold": 4000,
                "endpoints": {
                    "/api/v1/listings": {
                        "threshold": 8000,
                        "hard_cap": 20000,
                        "page_size": 25,
                        "summarization_enabled": False,
                    },
                    "/api/v1/bookings": {
                        "threshold": 6000,
                        "pagination_enabled": True,
                    },
                },
            }
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        service = ConfigService(config_path=config_file, auto_reload=False)

        assert "/api/v1/listings" in service.endpoint_overrides
        assert "/api/v1/bookings" in service.endpoint_overrides

        listings_override = service.endpoint_overrides["/api/v1/listings"]
        assert listings_override.threshold == 8000
        assert listings_override.hard_cap == 20000
        assert listings_override.page_size == 25
        assert listings_override.summarization_enabled is False

    def test_get_endpoint_config_with_override(self, tmp_path):
        """Test getting endpoint configuration with override."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "context_protection": {
                "output_token_threshold": 4000,
                "hard_output_token_cap": 12000,
                "default_page_size": 50,
                "endpoints": {
                    "/api/v1/listings": {
                        "threshold": 8000,
                        "page_size": 25,
                    },
                },
            }
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        service = ConfigService(config_path=config_file, auto_reload=False)

        threshold, hard_cap, page_size, summarization, pagination = service.get_endpoint_config(
            "/api/v1/listings"
        )

        assert threshold == 8000  # Override
        assert hard_cap == 12000  # Default
        assert page_size == 25  # Override
        assert summarization is True  # Default
        assert pagination is True  # Default

    def test_get_endpoint_config_without_override(self, tmp_path):
        """Test getting endpoint configuration without override (uses defaults)."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "context_protection": {
                "output_token_threshold": 4000,
                "hard_output_token_cap": 12000,
                "default_page_size": 50,
            }
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        service = ConfigService(config_path=config_file, auto_reload=False)

        threshold, hard_cap, page_size, summarization, pagination = service.get_endpoint_config(
            "/api/v1/unknown"
        )

        assert threshold == 4000
        assert hard_cap == 12000
        assert page_size == 50
        assert summarization is True
        assert pagination is True

    def test_load_config_empty_file(self, tmp_path):
        """Test loading from empty YAML file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        service = ConfigService(config_path=config_file, auto_reload=False)

        # Should use defaults
        assert service.config.output_token_threshold == 4000

    def test_load_config_invalid_yaml(self, tmp_path):
        """Test loading from invalid YAML file."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: {{")

        service = ConfigService(config_path=config_file, auto_reload=False)

        # Should use defaults on error
        assert service.config.output_token_threshold == 4000

    @pytest.mark.asyncio
    async def test_reload_config(self, tmp_path):
        """Test manual config reload."""
        config_file = tmp_path / "config.yaml"

        # Initial config
        config_data = {
            "context_protection": {
                "output_token_threshold": 4000,
            }
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        service = ConfigService(config_path=config_file, auto_reload=False)
        assert service.config.output_token_threshold == 4000

        # Update config
        config_data["context_protection"]["output_token_threshold"] = 6000
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Reload
        await service.reload_config()
        assert service.config.output_token_threshold == 6000

    def test_watcher_not_started_when_auto_reload_false(self, tmp_path):
        """Test file watcher is not started when auto_reload=False."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("context_protection: {}")

        service = ConfigService(config_path=config_file, auto_reload=False)

        assert service._observer is None

    def test_stop_watcher(self, tmp_path):
        """Test stopping file watcher."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("context_protection: {}")

        service = ConfigService(config_path=config_file, auto_reload=True)

        assert service._observer is not None

        service.stop_watcher()
        assert service._observer is None

    def test_stop_watcher_when_not_started(self):
        """Test stopping watcher when it was never started."""
        service = ConfigService(config_path="/nonexistent/path.yaml", auto_reload=False)

        # Should not raise error
        service.stop_watcher()
        assert service._observer is None


class TestGetConfigService:
    """Test suite for get_config_service singleton function."""

    def test_singleton_pattern(self, tmp_path):
        """Test that get_config_service returns same instance."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("context_protection: {}")

        # Reset global singleton
        import src.services.config_service

        src.services.config_service._config_service = None

        service1 = get_config_service(config_path=config_file, auto_reload=False)
        service2 = get_config_service(config_path=config_file, auto_reload=False)

        assert service1 is service2

    def test_singleton_initialization(self, tmp_path):
        """Test singleton is initialized on first call."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("context_protection: {}")

        # Reset global singleton
        import src.services.config_service

        src.services.config_service._config_service = None

        service = get_config_service(config_path=config_file, auto_reload=False)

        assert service is not None
        assert isinstance(service, ConfigService)
