import pytest

from disagreement.ext.commands.core import CommandHandler, Command, Group


class DummyBot:
    pass


@pytest.mark.asyncio
async def test_walk_commands_recurses_groups():
    bot = DummyBot()
    handler = CommandHandler(client=bot, prefix="!")

    async def root(ctx):
        pass

    root_group = Group(root, name="root")

    @root_group.command(name="child")
    async def child(ctx):
        pass

    @root_group.group(name="sub")
    async def sub(ctx):
        pass

    @sub.command(name="leaf")
    async def leaf(ctx):
        pass

    handler.add_command(root_group)

    names = [cmd.name for cmd in handler.walk_commands()]
    assert set(names) == {"help", "root", "child", "sub", "leaf"}
