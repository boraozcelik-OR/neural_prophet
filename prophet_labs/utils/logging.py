"""Centralised logging utilities for Prophet Labs."""
from __future__ import annotations

import logging
from logging import Logger
from typing import Optional


_LOGGER_CACHE: dict[str, Logger] = {}


class ContextFilter(logging.Filter):
    def __init__(self, correlation_id: Optional[str] = None):
        super().__init__()
        self.correlation_id = correlation_id or "-"

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.correlation_id = self.correlation_id
        return True


def configure_logging(level: str = "INFO", correlation_id: Optional[str] = None) -> None:
    """Configure root logging with structured friendly format."""

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] [corr=%(correlation_id)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(ContextFilter(correlation_id))
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers.clear()
    root.addHandler(handler)


def get_logger(name: str) -> Logger:
    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]
    logger = logging.getLogger(name)
    _LOGGER_CACHE[name] = logger
    return logger


__all__ = ["get_logger", "configure_logging", "ContextFilter"]
