"""Structured logging with correlation IDs for request tracing.

Provides JSON-formatted logs with correlation IDs to trace requests
across the entire application stack.
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger import jsonlogger

# Context variable to store correlation ID across async boundaries
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str:
    """Get current correlation ID or generate a new one.

    Returns:
        Current correlation ID from context or newly generated UUID
    """
    correlation_id = correlation_id_ctx.get()
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
        correlation_id_ctx.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context.

    Args:
        correlation_id: Correlation ID to set
    """
    correlation_id_ctx.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear correlation ID from current context."""
    correlation_id_ctx.set(None)


class CorrelationIdFilter(logging.Filter):
    """Logging filter that adds correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record.

        Args:
            record: Log record to modify

        Returns:
            Always True to pass the record through
        """
        record.correlation_id = get_correlation_id()  # type: ignore[attr-defined]
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to log record.

        Args:
            log_record: Dictionary to add fields to
            record: Original log record
            message_dict: Message dictionary
        """
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["correlation_id"] = getattr(record, "correlation_id", None)

        # Add exception info if present
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        # Add custom fields from record
        for key, value in message_dict.items():
            if key not in log_record:
                log_record[key] = value


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
) -> None:
    """Configure application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON formatting (default: True)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if json_format:
        # Use JSON formatter for structured logging
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(logger)s %(correlation_id)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    else:
        # Use standard formatter for development
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(correlation_id)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)

    # Add correlation ID filter
    correlation_filter = CorrelationIdFilter()
    console_handler.addFilter(correlation_filter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Silence noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Logging utilities for common operations


def log_api_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> None:
    """Log API request with structured data.

    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint
        params: Optional request parameters
    """
    logger.info(
        "API request",
        extra={
            "method": method,
            "endpoint": endpoint,
            "params": params or {},
            "event": "api_request",
        },
    )


def log_api_response(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
) -> None:
    """Log API response with structured data.

    Args:
        logger: Logger instance
        method: HTTP method
        endpoint: API endpoint
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
    """
    logger.info(
        "API response",
        extra={
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "event": "api_response",
        },
    )


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: dict[str, Any] | None = None,
) -> None:
    """Log error with structured context.

    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Optional context dictionary
    """
    logger.error(
        f"Error: {error!s}",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "event": "error",
        },
        exc_info=True,
    )


def log_auth_event(
    logger: logging.Logger,
    event_type: str,
    success: bool,
    details: dict[str, Any] | None = None,
) -> None:
    """Log authentication event.

    Args:
        logger: Logger instance
        event_type: Type of auth event (login, token_refresh, etc.)
        success: Whether the event succeeded
        details: Optional event details
    """
    logger.info(
        f"Auth event: {event_type}",
        extra={
            "auth_event_type": event_type,
            "success": success,
            "details": details or {},
            "event": "auth",
        },
    )
