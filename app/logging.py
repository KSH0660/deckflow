import logging
import os
from typing import Any

import structlog


def configure_logging(level: str = None) -> None:
    """
    Configure structlog with sensible defaults for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to INFO or LOG_LEVEL env var

    """
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Set standard library logging level
    logging.basicConfig(level=getattr(logging, level))
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a configured structlog logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """
    Bind context to all subsequent log messages in this execution context.

    Usage:
        bind_context(user_id="123", request_id="abc")
        logger.info("User action completed")  # Will include user_id and request_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


# Pre-configured logger for convenience
logger = get_logger(__name__)
