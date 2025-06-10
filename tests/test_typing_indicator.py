import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.client import Client
from disagreement.errors import DisagreementException


@pytest.mark.asyncio
async def test_typing_context_manager_calls_http():
    http = SimpleNamespace(trigger_typing=AsyncMock())
    client = Client.__new__(Client)
    client._http = http
    client._closed = False

    async with client.typing("123"):
        pass

    http.trigger_typing.assert_called_once_with("123")


@pytest.mark.asyncio
async def test_typing_closed():
    http = SimpleNamespace(trigger_typing=AsyncMock())
    client = Client.__new__(Client)
    client._http = http
    client._closed = True

    with pytest.raises(DisagreementException):
        async with client.typing("123"):
            pass


@pytest.mark.asyncio
async def test_context_typing():
    http = SimpleNamespace(trigger_typing=AsyncMock())

    class DummyBot:
        def __init__(self):
            self._http = http
            self._closed = False

        def typing(self, channel_id):
            from disagreement.typing import Typing

            return Typing(self, channel_id)

    bot = DummyBot()
    msg = SimpleNamespace(channel_id="c", id="1", guild_id=None, author=None)

    async def dummy(ctx):
        pass

    from disagreement.ext.commands.core import Command, CommandContext

    cmd = Command(dummy)
    ctx = CommandContext(
        message=msg, bot=bot, prefix="!", command=cmd, invoked_with="dummy"
    )

    async with ctx.typing():
        pass

    http.trigger_typing.assert_called_once_with("c")
