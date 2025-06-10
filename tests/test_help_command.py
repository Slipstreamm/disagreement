import pytest

from disagreement.ext.commands.core import CommandHandler, Command
from disagreement.models import Message


class DummyBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, channel_id, content, **kwargs):
        self.sent.append(content)
        return {"id": "1", "channel_id": channel_id, "content": content}


@pytest.mark.asyncio
async def test_help_lists_commands():
    bot = DummyBot()
    handler = CommandHandler(client=bot, prefix="!")

    async def foo(ctx):
        pass

    handler.add_command(Command(foo, name="foo", brief="Foo cmd"))

    msg_data = {
        "id": "1",
        "channel_id": "c",
        "author": {"id": "2", "username": "u", "discriminator": "0001"},
        "content": "!help",
        "timestamp": "t",
    }
    msg = Message(msg_data, client_instance=bot)
    await handler.process_commands(msg)
    assert any("foo" in m for m in bot.sent)


@pytest.mark.asyncio
async def test_help_specific_command():
    bot = DummyBot()
    handler = CommandHandler(client=bot, prefix="!")

    async def bar(ctx):
        pass

    handler.add_command(Command(bar, name="bar", description="Bar desc"))

    msg_data = {
        "id": "1",
        "channel_id": "c",
        "author": {"id": "2", "username": "u", "discriminator": "0001"},
        "content": "!help bar",
        "timestamp": "t",
    }
    msg = Message(msg_data, client_instance=bot)
    await handler.process_commands(msg)
    assert any("Bar desc" in m for m in bot.sent)
