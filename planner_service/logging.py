"""Structlog configuration for the planner service."""

import logging
import os
import sys

import structlog


def get_log_level() -> int:
    """Get log level from environment with safe default."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def configure_logging(service_name: str = "planner-service") -> None:
    """Configure structlog with service tag and standard processors.

    Args:
        service_name: Name of the service to include in log events.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if sys.stderr.isatty():
        # Development: pretty console output
        structlog.configure(
            processors=[
                *shared_processors,
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(get_log_level()),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Production: JSON output for Cloud Run
        structlog.configure(
            processors=[
                *shared_processors,
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(get_log_level()),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Set up stdlib logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=get_log_level(),
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a logger instance bound with service context.

    Args:
        name: Optional logger name (typically module name).

    Returns:
        A bound structlog logger with service tag.
    """
    logger = structlog.get_logger(name)
    return logger.bind(service="planner-service")
