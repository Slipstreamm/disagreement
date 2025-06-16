import pytest

from disagreement.client import Client
from disagreement.ext.commands.core import Command, CommandHandler
from disagreement.models import Message


class DummyBot:
    def __init__(self):
        self.executed = False


@pytest.mark.asyncio
async def test_get_context_parses_without_execution():
    bot = DummyBot()
    handler = CommandHandler(client=bot, prefix="!")

    async def foo(ctx, number: int, word: str):
        bot.executed = True

    handler.add_command(Command(foo, name="foo"))

    msg_data = {
        "id": "1",
        "channel_id": "c",
        "author": {"id": "2", "username": "u", "discriminator": "0001"},
        "content": "!foo 1 bar",
        "timestamp": "t",
    }
    msg = Message(msg_data, client_instance=bot)

    ctx = await handler.get_context(msg)
    assert ctx is not None
    assert ctx.command.name == "foo"
    assert ctx.args == [1, "bar"]
    assert bot.executed is False


@pytest.mark.asyncio
async def test_client_get_context():
    client = Client(token="t")

    async def foo(ctx):
        raise RuntimeError("should not run")

    client.command_handler.add_command(Command(foo, name="foo"))

    msg_data = {
        "id": "1",
        "channel_id": "c",
        "author": {"id": "2", "username": "u", "discriminator": "0001"},
        "content": "!foo",
        "timestamp": "t",
    }
    msg = Message(msg_data, client_instance=client)

    ctx = await client.get_context(msg)
    assert ctx is not None
    assert ctx.command.name == "foo"
