import asyncio
import pytest

from disagreement.client import Client
from disagreement.ext import commands


class DummyCog(commands.Cog):
    def __init__(self, client: Client) -> None:
        super().__init__(client)


@pytest.mark.asyncio()
async def test_command_handler_get_cog():
    bot = object()
    handler = commands.core.CommandHandler(client=bot, prefix="!")
    cog = DummyCog(bot)  # type: ignore[arg-type]
    handler.add_cog(cog)
    await asyncio.sleep(0)  # allow any scheduled tasks to start
    assert handler.get_cog("DummyCog") is cog


@pytest.mark.asyncio()
async def test_client_get_cog():
    client = Client(token="t")
    cog = DummyCog(client)
    client.add_cog(cog)
    await asyncio.sleep(0)
    assert client.get_cog("DummyCog") is cog
