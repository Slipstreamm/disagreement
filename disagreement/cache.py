from __future__ import annotations

import time
from typing import TYPE_CHECKING, Callable, Dict, Generic, Optional, TypeVar
from collections import OrderedDict

if TYPE_CHECKING:
    from .models import Channel, Guild, Member
    from .caching import MemberCacheFlags

T = TypeVar("T")


class Cache(Generic[T]):
    """Simple in-memory cache with optional TTL and max size support."""

    def __init__(
        self, ttl: Optional[float] = None, maxlen: Optional[int] = None
    ) -> None:
        self.ttl = ttl
        self.maxlen = maxlen
        self._data: "OrderedDict[str, tuple[T, Optional[float]]]" = OrderedDict()

    def set(self, key: str, value: T) -> None:
        expiry = time.monotonic() + self.ttl if self.ttl is not None else None
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = (value, expiry)
        if self.maxlen is not None and len(self._data) > self.maxlen:
            self._data.popitem(last=False)

    def get(self, key: str) -> Optional[T]:
        item = self._data.get(key)
        if not item:
            return None
        value, expiry = item
        if expiry is not None and expiry < time.monotonic():
            self.invalidate(key)
            return None
        self._data.move_to_end(key)
        return value

    def get_or_fetch(self, key: str, fetch_fn: Callable[[], T]) -> T:
        """Return a cached item or fetch and store it if missing."""
        value = self.get(key)
        if value is None:
            value = fetch_fn()
            self.set(key, value)
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


class MemberCache(Cache["Member"]):
    """
    A cache for :class:`Member` objects that respects :class:`MemberCacheFlags`.
    """

    def __init__(self, flags: MemberCacheFlags, ttl: Optional[float] = None) -> None:
        super().__init__(ttl)
        self.flags = flags

    def _should_cache(self, member: Member) -> bool:
        """Determines if a member should be cached based on the flags."""
        if self.flags.all:
            return True
        if self.flags.none:
            return False

        if self.flags.online and member.status != "offline":
            return True
        if self.flags.voice and member.voice_state is not None:
            return True
        if self.flags.joined and getattr(member, "_just_joined", False):
            return True
        return False

    def set(self, key: str, value: Member) -> None:
        if self._should_cache(value):
            super().set(key, value)
