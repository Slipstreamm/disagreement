import asyncio
import pytest

from disagreement.ext.commands.core import CommandHandler
from disagreement.ext.commands.decorators import command, max_concurrency
from disagreement.ext.commands.errors import MaxConcurrencyReached
from disagreement.models import Message


class DummyBot:
    def __init__(self):
        self.errors = []

    async def on_command_error(self, ctx, error):
        self.errors.append(error)


@pytest.mark.asyncio
async def test_max_concurrency_per_user():
    bot = DummyBot()
    handler = CommandHandler(client=bot, prefix="!")
    started = asyncio.Event()
    release = asyncio.Event()

    @command()
    @max_concurrency(1, per="user")
    async def foo(ctx):
        started.set()
        await release.wait()

    handler.add_command(foo.__command_object__)

    data = {
        "id": "1",
        "channel_id": "c",
        "guild_id": "g",
        "author": {"id": "a", "username": "u", "discriminator": "0001"},
        "content": "!foo",
        "timestamp": "t",
    }
    msg1 = Message(data, client_instance=bot)
    msg2 = Message({**data, "id": "2"}, client_instance=bot)

    task = asyncio.create_task(handler.process_commands(msg1))
    await started.wait()

    await handler.process_commands(msg2)
    assert any(isinstance(e, MaxConcurrencyReached) for e in bot.errors)

    release.set()
    await task

    await handler.process_commands(msg2)


@pytest.mark.asyncio
async def test_max_concurrency_per_guild():
    bot = DummyBot()
    handler = CommandHandler(client=bot, prefix="!")
    started = asyncio.Event()
    release = asyncio.Event()

    @command()
    @max_concurrency(1, per="guild")
    async def foo(ctx):
        started.set()
        await release.wait()

    handler.add_command(foo.__command_object__)

    base = {
        "channel_id": "c",
        "guild_id": "g",
        "content": "!foo",
        "timestamp": "t",
    }
    msg1 = Message(
        {
            **base,
            "id": "1",
            "author": {"id": "a", "username": "u", "discriminator": "0001"},
        },
        client_instance=bot,
    )
    msg2 = Message(
        {
            **base,
            "id": "2",
            "author": {"id": "b", "username": "v", "discriminator": "0001"},
        },
        client_instance=bot,
    )

    task = asyncio.create_task(handler.process_commands(msg1))
    await started.wait()

    await handler.process_commands(msg2)
    assert any(isinstance(e, MaxConcurrencyReached) for e in bot.errors)

    release.set()
    await task

    await handler.process_commands(msg2)
