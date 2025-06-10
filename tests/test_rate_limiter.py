import asyncio
import time

import pytest

from disagreement.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_route_rate_limit_sleep():
    rl = RateLimiter()
    task = asyncio.create_task(rl.handle_rate_limit("GET:/a", 0.05, False))
    await asyncio.sleep(0)  # ensure task starts
    start = time.monotonic()
    await rl.acquire("GET:/a")
    duration = time.monotonic() - start
    await task
    assert duration >= 0.05


@pytest.mark.asyncio
async def test_global_rate_limit_blocks_all_routes():
    rl = RateLimiter()
    task = asyncio.create_task(rl.handle_rate_limit("GET:/a", 0.05, True))
    await asyncio.sleep(0)
    start = time.monotonic()
    await rl.acquire("POST:/b")
    duration = time.monotonic() - start
    await task
    assert duration >= 0.05
