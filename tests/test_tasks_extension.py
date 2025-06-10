import asyncio

import pytest

from disagreement.ext import tasks


class Dummy:
    def __init__(self) -> None:
        self.count = 0

    @tasks.loop(seconds=0.01)
    async def work(self) -> None:
        self.count += 1


@pytest.mark.asyncio
async def test_loop_runs_and_stops() -> None:
    dummy = Dummy()
    dummy.work.start()  # pylint: disable=no-member
    await asyncio.sleep(0.05)
    dummy.work.stop()  # pylint: disable=no-member
    assert dummy.count >= 2
    assert not dummy.work.running  # pylint: disable=no-member
