"""Compatibility layer for structured logging utilities."""
from __future__ import annotations

from logging import Logger
from typing import Optional

from prophet_labs.utils.logging_config import (
    ContextFilter,
    LoggingConfig,
    get_logger,
    init_logging,
)


def configure_logging(level: str = "INFO", correlation_id: Optional[str] = None) -> None:
    """Configure logging using the structured logging backend.

    Kept for backward compatibility; delegates to ``init_logging`` and injects
    a default correlation id if provided.
    """

    config = LoggingConfig(default_level=level)
    init_logging(config)
    if correlation_id:
        logger = get_logger("prophet_labs.app")
        logger.addFilter(ContextFilter(correlation_id))


__all__ = ["get_logger", "configure_logging", "ContextFilter", "LoggingConfig", "init_logging"]
