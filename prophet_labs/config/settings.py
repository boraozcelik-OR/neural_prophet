"""Typed configuration management for Prophet Labs.

Provides a Pydantic-based settings layer for environment configuration and
helpers for loading YAML configuration files. Defaults are designed so the
platform can run locally with SQLite and in-memory cache while enabling Redis
and production backends when configured via environment variables.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseSettings, Field, validator


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_sqlite_url() -> str:
    path = _repo_root().joinpath("..", "data", "prophet_labs.db").resolve()
    return f"sqlite:///{path}"


class ProphetLabsSettings(BaseSettings):
    """Base configuration for Prophet Labs.

    Environment variables are prefixed with ``PROPHET_LABS_``. Paths are
    resolved relative to the repository root when provided as relative strings.
    """

    environment: str = Field("development", description="Runtime environment name")
    log_level: str = Field("INFO", description="Root log level")

    database_url: str = Field(default_factory=_default_sqlite_url, description="SQLAlchemy database URL")
    redis_url: Optional[str] = Field(None, description="Redis URL for caching and background jobs")
    cache_enabled: bool = Field(True, description="Toggle caching layer")
    job_backend: str = Field("apscheduler", description="Job backend selection: apscheduler|celery|rq")

    api_host: str = Field("0.0.0.0", description="API bind host")
    api_port: int = Field(8000, description="API bind port")
    api_base_path: str = Field("/api/v1", description="Base path for versioned API")

    data_dir: Path = Field(default=Path("data"), description="Directory for normalized datasets")
    models_dir: Path = Field(default=Path("models"), description="Directory for trained models")
    outputs_dir: Path = Field(default=Path("outputs"), description="Directory for generated reports and forecasts")

    metrics_enabled: bool = Field(True, description="Expose Prometheus metrics endpoint")
    enable_security: bool = Field(False, description="Require auth dependencies when True")
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"], description="CORS allowed origins")
    sentry_dsn: Optional[str] = Field(None, description="Optional Sentry DSN for error reporting")

    class Config:
        env_prefix = "PROPHET_LABS_"
        env_file = ".env"
        case_sensitive = False

    @validator("api_base_path")
    def _strip_trailing_slash(cls, value: str) -> str:  # noqa: N805
        return value[:-1] if value.endswith("/") else value

    def resolved_path(self, value: Path) -> Path:
        return value if value.is_absolute() else _repo_root().joinpath(value)

    @property
    def data_path(self) -> Path:
        return self.resolved_path(self.data_dir)

    @property
    def models_path(self) -> Path:
        return self.resolved_path(self.models_dir)

    @property
    def outputs_path(self) -> Path:
        return self.resolved_path(self.outputs_dir)


@lru_cache(maxsize=1)
def get_settings() -> ProphetLabsSettings:
    """Singleton accessor to avoid repeated environment parsing."""

    settings = ProphetLabsSettings()
    settings.data_path.mkdir(parents=True, exist_ok=True)
    settings.models_path.mkdir(parents=True, exist_ok=True)
    settings.outputs_path.mkdir(parents=True, exist_ok=True)
    return settings


def _load_yaml_config(name: str) -> Dict[str, Any]:
    config_dir = _repo_root().joinpath("config")
    path = config_dir.joinpath(name)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_categories() -> Dict[str, Any]:
    return _load_yaml_config("categories.yaml")


def load_thresholds() -> Dict[str, Any]:
    return _load_yaml_config("thresholds.yaml")


def load_sources() -> Dict[str, Any]:
    return _load_yaml_config("sources.yaml")


__all__ = [
    "ProphetLabsSettings",
    "get_settings",
    "load_categories",
    "load_thresholds",
    "load_sources",
]
