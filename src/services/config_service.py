"""Configuration service for token budget management.

Provides hot-reload capability for token budget configuration using file watcher.
Based on research.md R004: Watchdog file watcher with atomic swap.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.models.token_budget import EndpointBudgetOverride, TokenBudgetConfig

logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for config changes."""

    def __init__(self, callback: Any) -> None:
        """Initialize handler.

        Args:
            callback: Async function to call on config change
        """
        self.callback = callback
        self._last_modified = 0.0

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        # Debounce rapid file changes
        import time

        current_time = time.time()
        if current_time - self._last_modified < 1.0:
            return

        self._last_modified = current_time

        # Schedule callback in event loop
        try:
            asyncio.create_task(self.callback())
        except RuntimeError:
            # No event loop running
            logger.warning("No event loop available for config reload")


class ConfigService:
    """Service for token budget configuration management.

    Supports hot-reload from YAML file using watchdog file watcher.

    Attributes:
        config_path: Path to configuration file
        config: Current token budget configuration
        endpoint_overrides: Per-endpoint budget overrides
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        auto_reload: bool = True,
    ) -> None:
        """Initialize config service.

        Args:
            config_path: Path to config file (uses default if None)
            auto_reload: Enable automatic config reload on file change
        """
        if config_path is None:
            config_path = Path("/opt/hostaway-mcp/config.yaml")
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.auto_reload = auto_reload

        # Load initial config
        self.config = TokenBudgetConfig()
        self.endpoint_overrides: dict[str, EndpointBudgetOverride] = {}

        if self.config_path.exists():
            self._load_config()

        # Setup file watcher
        self._observer: Observer | None = None
        if self.auto_reload and self.config_path.exists():
            self._start_watcher()

    def _load_config(self) -> None:
        """Load configuration from file.

        Performs atomic swap of config object on successful load.
        """
        try:
            with open(self.config_path) as f:
                config_data = yaml.safe_load(f)

            if config_data is None:
                logger.warning("Empty config file, using defaults")
                return

            # Parse main config
            context_protection = config_data.get("context_protection", {})
            new_config = TokenBudgetConfig(
                output_token_threshold=context_protection.get(
                    "output_token_threshold", 4000
                ),
                hard_output_token_cap=context_protection.get("hard_output_token_cap", 12000),
                default_page_size=context_protection.get("default_page_size", 50),
                max_page_size=context_protection.get("max_page_size", 200),
                enable_summarization=context_protection.get("enable_summarization", True),
                enable_pagination=context_protection.get("enable_pagination", True),
            )

            # Parse endpoint overrides
            new_overrides: dict[str, EndpointBudgetOverride] = {}
            endpoints = context_protection.get("endpoints", {})
            for pattern, override_data in endpoints.items():
                try:
                    override = EndpointBudgetOverride(
                        endpoint_pattern=pattern,
                        threshold=override_data.get("threshold"),
                        hard_cap=override_data.get("hard_cap"),
                        page_size=override_data.get("page_size"),
                        summarization_enabled=override_data.get("summarization_enabled"),
                        pagination_enabled=override_data.get("pagination_enabled"),
                    )
                    new_overrides[pattern] = override
                except ValidationError as e:
                    logger.error(f"Invalid endpoint override for {pattern}: {e}")

            # Atomic swap
            self.config = new_config
            self.endpoint_overrides = new_overrides

            logger.info(f"Config loaded from {self.config_path}")

        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            logger.error(f"YAML parse error: {e}")
        except ValidationError as e:
            logger.error(f"Config validation error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")

    async def reload_config(self) -> None:
        """Reload configuration from file (async).

        Can be called manually or triggered by file watcher.
        """
        logger.info("Reloading config...")
        self._load_config()

    def _start_watcher(self) -> None:
        """Start file watcher for config changes."""
        event_handler = ConfigFileHandler(callback=self.reload_config)
        self._observer = Observer()
        self._observer.schedule(
            event_handler,
            path=str(self.config_path.parent),
            recursive=False,
        )
        self._observer.start()
        logger.info(f"Config watcher started for {self.config_path}")

    def stop_watcher(self) -> None:
        """Stop file watcher."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Config watcher stopped")

    def get_endpoint_config(
        self,
        endpoint_path: str,
    ) -> tuple[int, int, int, bool, bool]:
        """Get effective configuration for an endpoint.

        Applies endpoint-specific overrides if available, otherwise uses defaults.

        Args:
            endpoint_path: API endpoint path (e.g., "/api/v1/listings")

        Returns:
            Tuple of (threshold, hard_cap, page_size, summarization_enabled, pagination_enabled)
        """
        # Check for exact match
        override = self.endpoint_overrides.get(endpoint_path)

        # Apply overrides or use defaults
        threshold = (
            override.threshold if override and override.threshold is not None
            else self.config.output_token_threshold
        )
        hard_cap = (
            override.hard_cap if override and override.hard_cap is not None
            else self.config.hard_output_token_cap
        )
        page_size = (
            override.page_size if override and override.page_size is not None
            else self.config.default_page_size
        )
        summarization_enabled = (
            override.summarization_enabled
            if override and override.summarization_enabled is not None
            else self.config.enable_summarization
        )
        pagination_enabled = (
            override.pagination_enabled
            if override and override.pagination_enabled is not None
            else self.config.enable_pagination
        )

        return threshold, hard_cap, page_size, summarization_enabled, pagination_enabled


# Global singleton instance
_config_service: ConfigService | None = None


def get_config_service(
    config_path: str | Path | None = None,
    auto_reload: bool = True,
) -> ConfigService:
    """Get global config service instance.

    Args:
        config_path: Path to config file
        auto_reload: Enable auto-reload

    Returns:
        Singleton ConfigService instance
    """
    global _config_service

    if _config_service is None:
        _config_service = ConfigService(
            config_path=config_path,
            auto_reload=auto_reload,
        )

    return _config_service
