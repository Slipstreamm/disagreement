import pytest
from unittest.mock import AsyncMock

from disagreement.event_dispatcher import EventDispatcher


class DummyClient:
    pass


@pytest.mark.asyncio
async def test_dispatch_error_hook_called():
    dispatcher = EventDispatcher(DummyClient())
    hook = AsyncMock()
    dispatcher.on_dispatch_error = hook

    async def listener(_):
        raise RuntimeError("boom")

    dispatcher.register("TEST_EVENT", listener)
    await dispatcher.dispatch("TEST_EVENT", {})

    hook.assert_awaited_once()
    args = hook.call_args.args
    assert args[0] == "TEST_EVENT"
    assert isinstance(args[1], RuntimeError)
    assert args[2] is listener


@pytest.mark.asyncio
async def test_dispatch_error_hook_not_called_when_ok():
    dispatcher = EventDispatcher(DummyClient())
    hook = AsyncMock()
    dispatcher.on_dispatch_error = hook

    async def listener(_):
        return

    dispatcher.register("TEST_EVENT", listener)
    await dispatcher.dispatch("TEST_EVENT", {})

    hook.assert_not_awaited()
