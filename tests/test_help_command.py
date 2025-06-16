import pytest

from disagreement.ext import commands
from disagreement.ext.commands.core import CommandHandler, Command, Group
from disagreement.models import Message


class DummyBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, channel_id, content, **kwargs):
        self.sent.append(content)
        return {"id": "1", "channel_id": channel_id, "content": content}


class MyCog(commands.Cog):
    def __init__(self, client) -> None:
        super().__init__(client)

    @commands.command()
    async def foo(self, ctx: commands.CommandContext) -> None:
        pass


@pytest.mark.asyncio
async def test_help_lists_commands():
    bot = DummyBot()
    handler = CommandHandler(client=bot, prefix="!")

    handler.add_cog(MyCog(bot))

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
    assert any("MyCog" in m for m in bot.sent)


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


from disagreement.ext.commands.help import HelpCommand


class CustomHelp(HelpCommand):
    async def send_command_help(self, ctx, command):
        await ctx.send(f"custom {command.name}")

    async def send_group_help(self, ctx, group):
        await ctx.send(f"group {group.name}")


@pytest.mark.asyncio
async def test_custom_help_methods():
    bot = DummyBot()
    handler = CommandHandler(client=bot, prefix="!")
    handler.remove_command("help")
    handler.add_command(CustomHelp(handler))

    async def sub(ctx):
        pass

    group = Group(sub, name="grp")
    handler.add_command(group)

    msg_data = {
        "id": "1",
        "channel_id": "c",
        "author": {"id": "2", "username": "u", "discriminator": "0001"},
        "content": "!help grp",
        "timestamp": "t",
    }
    msg = Message(msg_data, client_instance=bot)
    await handler.process_commands(msg)
    assert any("group grp" in m for m in bot.sent)
