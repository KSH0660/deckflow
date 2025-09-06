import logging
import os
from typing import Any

import structlog


def compact_renderer(logger, name, event_dict):
    """Compact renderer for cleaner log output."""
    level = event_dict.get("level", "").upper()
    timestamp = event_dict.get("timestamp", "")
    event = event_dict.get("event", "")

    # Extract just the module name (e.g., write_slide_content instead of app.service.module.write_slide_content)
    logger_name = name or ""
    if "." in logger_name:
        logger_name = logger_name.split(".")[-1]

    # Format timestamp to be shorter (just time, no date/timezone)
    if "T" in timestamp:
        time_part = timestamp.split("T")[1]
        if "." in time_part:
            time_part = time_part.split(".")[0]  # Remove microseconds
        timestamp = time_part

    # Build compact log line
    log_parts = []

    # Add level and time
    if level:
        log_parts.append(f"[{level[:1]}]")  # Just first letter: [I], [E], [D]
    if timestamp:
        log_parts.append(f"{timestamp}")
    if logger_name:
        log_parts.append(f"[{logger_name}]")

    # Add main message
    if event:
        log_parts.append(event)

    # Add other key-value pairs in compact format
    for key, value in event_dict.items():
        if key not in ["level", "timestamp", "event", "logger"]:
            if isinstance(value, str) and len(value) > 50:
                value = f"{value[:47]}..."
            log_parts.append(f"{key}={value}")

    return " ".join(log_parts)


def configure_logging(level: str = None, compact: bool = True) -> None:
    """
    Configure structlog with sensible defaults for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to INFO or LOG_LEVEL env var
        compact: Use compact logging format (default True)

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

    # Choose renderer based on compact setting
    if compact:
        processors.append(compact_renderer)
    else:
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
