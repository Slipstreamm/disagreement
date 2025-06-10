from __future__ import annotations

import time
from typing import TYPE_CHECKING, Dict, Generic, Optional, TypeVar

if TYPE_CHECKING:
    from .models import Channel, Guild

T = TypeVar("T")


class Cache(Generic[T]):
    """Simple in-memory cache with optional TTL support."""

    def __init__(self, ttl: Optional[float] = None) -> None:
        self.ttl = ttl
        self._data: Dict[str, tuple[T, Optional[float]]] = {}

    def set(self, key: str, value: T) -> None:
        expiry = time.monotonic() + self.ttl if self.ttl is not None else None
        self._data[key] = (value, expiry)

    def get(self, key: str) -> Optional[T]:
        item = self._data.get(key)
        if not item:
            return None
        value, expiry = item
        if expiry is not None and expiry < time.monotonic():
            self.invalidate(key)
            return None
        return value

    def invalidate(self, key: str) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()

    def values(self) -> list[T]:
        now = time.monotonic()
        items = []
        for key, (value, expiry) in list(self._data.items()):
            if expiry is not None and expiry < now:
                self.invalidate(key)
            else:
                items.append(value)
        return items


class GuildCache(Cache["Guild"]):
    """Cache specifically for :class:`Guild` objects."""


class ChannelCache(Cache["Channel"]):
    """Cache specifically for :class:`Channel` objects."""
