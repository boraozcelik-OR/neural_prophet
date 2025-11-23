"""Structured logging configuration for Prophet Labs.

Provides per-domain loggers writing to rotating files under ``logs/`` with
optional console output. The formatter injects correlation and user context
plus JSON-encoded extra fields to keep logs machine-readable while still
human-friendly.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from logging import Logger
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Dict, Iterable
import time

# Default logger names and their corresponding log file names
_LOGGER_FILES: Dict[str, str] = {
    "prophet_labs.app": "app.log",
    "prophet_labs.ingestion": "ingestion.log",
    "prophet_labs.forecast": "forecast.log",
    "prophet_labs.accuracy": "accuracy.log",
    "prophet_labs.ui": "ui.log",
    "prophet_labs.audit": "audit.log",
}

_STANDARD_ATTRS: set[str] = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


@dataclass
class LoggingConfig:
    """Runtime logging configuration."""

    logs_dir: Path = Path("logs")
    rotation_type: str = "size"  # "size" or "time"
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 7
    rotation_when: str = "midnight"
    rotation_interval: int = 1
    log_to_console: bool = False
    default_level: str = "INFO"
    levels: Dict[str, str] = field(
        default_factory=lambda: {
            "prophet_labs.app": "INFO",
            "prophet_labs.ingestion": "INFO",
            "prophet_labs.forecast": "INFO",
            "prophet_labs.accuracy": "INFO",
            "prophet_labs.ui": "INFO",
            "prophet_labs.audit": "INFO",
        }
    )

    def level_for(self, name: str) -> str:
        return self.levels.get(name, self.default_level).upper()

    @property
    def all_logger_names(self) -> Iterable[str]:
        return _LOGGER_FILES.keys()


class ContextFilter(logging.Filter):
    """Inject default context fields for structured logging."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.correlation_id = getattr(record, "correlation_id", "-") or "-"
        record.user_id = getattr(record, "user_id", "SYSTEM") or "SYSTEM"
        extra_fields = getattr(record, "extra_fields", {})
        if not isinstance(extra_fields, dict):
            extra_fields = {"extra_fields": str(extra_fields)}
        record.extra_json = json.dumps(extra_fields, default=str)
        return True


class StructuredFormatter(logging.Formatter):
    """Formatter producing stable, parse-friendly log lines in UTC."""

    converter = time.gmtime

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)s | %(name)s | corr=%(correlation_id)s | user=%(user_id)s | %(message)s | %(extra_json)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        # Consolidate non-standard attributes into extra_fields if not provided
        if not hasattr(record, "extra_fields"):
            extras = {
                k: v
                for k, v in record.__dict__.items()
                if k not in _STANDARD_ATTRS
                and not k.startswith("_")
                and k
                not in {
                    "correlation_id",
                    "user_id",
                    "extra_json",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "stacklevel",
                }
            }
            record.extra_fields = extras
        return super().format(record)


def _build_file_handler(path: Path, config: LoggingConfig, formatter: logging.Formatter) -> logging.Handler:
    path.parent.mkdir(parents=True, exist_ok=True)
    if config.rotation_type.lower() == "time":
        handler: logging.Handler = TimedRotatingFileHandler(
            path,
            when=config.rotation_when,
            interval=config.rotation_interval,
            backupCount=config.backup_count,
            utc=True,
        )
    else:
        handler = RotatingFileHandler(
            path, maxBytes=config.max_bytes, backupCount=config.backup_count
        )
    handler.setFormatter(formatter)
    handler.addFilter(ContextFilter())
    return handler


_initialized = False


def init_logging(config: LoggingConfig | None = None) -> None:
    """Initialise structured loggers for Prophet Labs.

    Safe to call multiple times; subsequent calls overwrite handler
    configuration with the provided config.
    """

    global _initialized
    cfg = config or LoggingConfig()
    formatter = StructuredFormatter()
    cfg.logs_dir.mkdir(parents=True, exist_ok=True)

    for name, filename in _LOGGER_FILES.items():
        logger = logging.getLogger(name)
        logger.setLevel(cfg.level_for(name))
        logger.handlers.clear()
        logger.propagate = False
        file_handler = _build_file_handler(cfg.logs_dir / filename, cfg, formatter)
        logger.addHandler(file_handler)
        if cfg.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.addFilter(ContextFilter())
            logger.addHandler(console_handler)

    # Root logger: ensure it does not emit duplicate records beyond configured loggers
    root_logger = logging.getLogger()
    root_logger.setLevel(cfg.default_level.upper())
    root_logger.handlers.clear()
    if cfg.log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.addFilter(ContextFilter())
        root_logger.addHandler(console_handler)

    _initialized = True


def get_logger(name: str) -> Logger:
    """Retrieve a configured logger (initialising defaults on first use)."""

    global _initialized
    if not _initialized:
        init_logging()
    return logging.getLogger(name)


__all__ = ["LoggingConfig", "init_logging", "get_logger", "ContextFilter", "StructuredFormatter"]
