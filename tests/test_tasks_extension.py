import asyncio
import datetime

import pytest

from disagreement.ext import tasks


class Dummy:
    def __init__(self) -> None:
        self.count = 0

    @tasks.loop(seconds=0.01)
    async def work(self) -> None:
        self.count += 1


@pytest.mark.asyncio
async def test_loop_on_error_callback_called() -> None:
    called = False

    def handler(exc: Exception) -> None:  # pragma: no cover - simple callback
        nonlocal called
        called = True

    @tasks.loop(seconds=0.01, on_error=handler)
    async def failing() -> None:
        raise RuntimeError("fail")

    failing.start()
    await asyncio.sleep(0.03)
    failing.stop()
    assert called


@pytest.mark.asyncio
async def test_loop_time_of_day() -> None:
    run_count = 0

    target_time = (datetime.datetime.now() + datetime.timedelta(seconds=0.05)).time()

    @tasks.loop(time_of_day=target_time)
    async def daily() -> None:
        nonlocal run_count
        run_count += 1

    daily.start()
    await asyncio.sleep(0.1)
    daily.stop()
    assert run_count >= 1


@pytest.mark.asyncio
async def test_loop_runs_and_stops() -> None:
    dummy = Dummy()
    dummy.work.start()  # pylint: disable=no-member
    await asyncio.sleep(0.05)
    dummy.work.stop()  # pylint: disable=no-member
    assert dummy.count >= 2
    assert not dummy.work.running  # pylint: disable=no-member


@pytest.mark.asyncio
async def test_before_after_loop_callbacks() -> None:
    events: list[str] = []

    @tasks.loop(seconds=0.01)
    async def ticker() -> None:
        events.append("tick")

    @ticker.before_loop
    async def before() -> None:  # pragma: no cover - trivial callback
        events.append("before")

    @ticker.after_loop
    async def after() -> None:  # pragma: no cover - trivial callback
        events.append("after")

    ticker.start()
    await asyncio.sleep(0.03)
    ticker.stop()
    await asyncio.sleep(0.01)
    assert events and events[0] == "before"
    assert "after" in events
