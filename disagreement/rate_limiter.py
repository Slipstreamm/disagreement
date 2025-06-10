"""Asynchronous rate limiter for Discord HTTP requests."""

from __future__ import annotations

import asyncio
import time
from typing import Dict, Mapping


class _Bucket:
    def __init__(self) -> None:
        self.remaining: int = 1
        self.reset_at: float = 0.0
        self.lock = asyncio.Lock()


class RateLimiter:
    """Rate limiter implementing per-route buckets and a global queue."""

    def __init__(self) -> None:
        self._buckets: Dict[str, _Bucket] = {}
        self._global_event = asyncio.Event()
        self._global_event.set()

    def _get_bucket(self, route: str) -> _Bucket:
        bucket = self._buckets.get(route)
        if bucket is None:
            bucket = _Bucket()
            self._buckets[route] = bucket
        return bucket

    async def acquire(self, route: str) -> _Bucket:
        bucket = self._get_bucket(route)
        while True:
            await self._global_event.wait()
            async with bucket.lock:
                now = time.monotonic()
                if bucket.remaining <= 0 and now < bucket.reset_at:
                    await asyncio.sleep(bucket.reset_at - now)
                    continue
                if bucket.remaining > 0:
                    bucket.remaining -= 1
                return bucket

    def release(self, route: str, headers: Mapping[str, str]) -> None:
        bucket = self._get_bucket(route)
        try:
            remaining = int(headers.get("X-RateLimit-Remaining", bucket.remaining))
            reset_after = float(headers.get("X-RateLimit-Reset-After", "0"))
            bucket.remaining = remaining
            bucket.reset_at = time.monotonic() + reset_after
        except ValueError:
            pass

        if headers.get("X-RateLimit-Global", "false").lower() == "true":
            retry_after = float(headers.get("Retry-After", "0"))
            self._global_event.clear()
            asyncio.create_task(self._lift_global(retry_after))

    async def handle_rate_limit(
        self, route: str, retry_after: float, is_global: bool
    ) -> None:
        bucket = self._get_bucket(route)
        bucket.remaining = 0
        bucket.reset_at = time.monotonic() + retry_after
        if is_global:
            self._global_event.clear()
            await asyncio.sleep(retry_after)
            self._global_event.set()
        else:
            await asyncio.sleep(retry_after)

    async def _lift_global(self, delay: float) -> None:
        await asyncio.sleep(delay)
        self._global_event.set()
