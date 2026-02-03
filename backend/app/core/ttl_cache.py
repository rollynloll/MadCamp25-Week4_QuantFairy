from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass
class _CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    """Simple in-memory TTL cache for short-lived API responses."""

    def __init__(self, default_ttl: float = 10.0, maxsize: int = 256) -> None:
        self.default_ttl = default_ttl
        self.maxsize = maxsize
        self._store: Dict[str, _CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.monotonic():
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        if len(self._store) >= self.maxsize:
            self._prune()
        expires_at = time.monotonic() + (ttl if ttl is not None else self.default_ttl)
        self._store[key] = _CacheEntry(value=value, expires_at=expires_at)

    def get_or_set(self, key: str, loader: Callable[[], Any], ttl: float | None = None) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = loader()
        self.set(key, value, ttl=ttl)
        return value

    def _prune(self) -> None:
        now = time.monotonic()
        expired_keys = [key for key, entry in self._store.items() if entry.expires_at < now]
        for key in expired_keys:
            self._store.pop(key, None)
        if len(self._store) >= self.maxsize and self._store:
            self._store.pop(next(iter(self._store)), None)
