"""Cache abstraction for Prophet Labs.

Provides Redis-backed cache when configured with a safe in-memory fallback to
keep the platform functional without external infrastructure.
"""
from __future__ import annotations

import json
import time
from typing import Any, Optional

try:  # Optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional import
    redis = None

from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


class BaseCache:
    def get(self, key: str) -> Optional[str]:  # pragma: no cover - interface
        raise NotImplementedError

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def delete(self, key: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class InMemoryCache(BaseCache):
    def __init__(self) -> None:
        self._store: dict[str, tuple[str, Optional[float]]] = {}

    def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if not entry:
            return None
        value, expires_at = entry
        if expires_at is not None and expires_at < time.time():
            self.delete(key)
            return None
        return value

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]


class RedisCache(BaseCache):
    def __init__(self, url: str):
        if redis is None:
            raise RuntimeError("redis library not installed")
        self._client = redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[str]:
        return self._client.get(key)

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        if ttl_seconds:
            self._client.setex(key, ttl_seconds, value)
        else:
            self._client.set(key, value)

    def delete(self, key: str) -> None:
        self._client.delete(key)


class CacheFacade:
    """Lightweight cache façade with JSON helpers."""

    def __init__(self, backend: BaseCache):
        self._backend = backend

    def get_json(self, key: str) -> Optional[Any]:
        raw = self._backend.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:  # pragma: no cover - defensive
            LOGGER.warning("Failed to parse cached JSON", extra={"key": key})
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        try:
            encoded = json.dumps(value, default=str)
        except TypeError:
            LOGGER.warning("Value not JSON serializable; skipping cache", extra={"key": key})
            return
        self._backend.set(key, encoded, ttl_seconds=ttl_seconds)

    def delete(self, key: str) -> None:
        self._backend.delete(key)


def build_cache(redis_url: Optional[str], enabled: bool = True) -> CacheFacade:
    if not enabled:
        return CacheFacade(InMemoryCache())
    if redis_url:
        try:
            return CacheFacade(RedisCache(redis_url))
        except Exception as exc:  # pragma: no cover - runtime safeguard
            LOGGER.warning("Falling back to in-memory cache", exc_info=exc)
    return CacheFacade(InMemoryCache())


__all__ = ["CacheFacade", "build_cache", "BaseCache", "RedisCache", "InMemoryCache"]
