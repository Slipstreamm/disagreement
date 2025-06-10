import asyncio
import pytest

from disagreement.ext.commands.core import Command, CommandContext
from disagreement.ext.commands.decorators import (
    check,
    cooldown,
    requires_permissions,
)
from disagreement.ext.commands.errors import CheckFailure, CommandOnCooldown
from disagreement.permissions import Permissions


@pytest.mark.asyncio
async def test_check_decorator_blocks(message):
    async def cb(ctx):
        pass

    cmd = Command(check(lambda c: False)(cb))
    ctx = CommandContext(
        message=message,
        bot=message._client,
        prefix="!",
        command=cmd,
        invoked_with="test",
    )

    with pytest.raises(CheckFailure):
        await cmd.invoke(ctx)


@pytest.mark.asyncio
async def test_cooldown_per_user(message):
    uses = []

    @cooldown(1, 0.1)
    async def cb(ctx):
        uses.append(1)

    cmd = Command(cb)
    ctx = CommandContext(
        message=message,
        bot=message._client,
        prefix="!",
        command=cmd,
        invoked_with="test",
    )

    await cmd.invoke(ctx)

    with pytest.raises(CommandOnCooldown):
        await cmd.invoke(ctx)

    await asyncio.sleep(0.1)
    await cmd.invoke(ctx)
    assert len(uses) == 2


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_requires_permissions_pass(message):
    class Guild:
        id = "g"
        owner_id = "owner"
        roles = []

        def get_member(self, mid):
            return message.author

    class Channel:
        def __init__(self, perms):
            self.perms = perms
            self.guild_id = "g"

        def permissions_for(self, member):
            return self.perms

    message.author.roles = []
    message._client.get_channel = lambda cid: Channel(Permissions.SEND_MESSAGES)
    message._client.get_guild = lambda gid: Guild()

    @requires_permissions(Permissions.SEND_MESSAGES)
    async def cb(ctx):
        pass

    cmd = Command(cb)
    ctx = CommandContext(
        message=message,
        bot=message._client,
        prefix="!",
        command=cmd,
        invoked_with="test",
    )

    await cmd.invoke(ctx)

@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_requires_permissions_fail(message):
    class Guild:
        id = "g"
        owner_id = "owner"
        roles = []

        def get_member(self, mid):
            return message.author

    class Channel:
        def __init__(self, perms):
            self.perms = perms
            self.guild_id = "g"

        def permissions_for(self, member):
            return self.perms

    message.author.roles = []
    message._client.get_channel = lambda cid: Channel(Permissions.SEND_MESSAGES)
    message._client.get_guild = lambda gid: Guild()

    @requires_permissions(Permissions.MANAGE_MESSAGES)
    async def cb(ctx):
        pass

    cmd = Command(cb)
    ctx = CommandContext(
        message=message,
        bot=message._client,
        prefix="!",
        command=cmd,
        invoked_with="test",
    )

    with pytest.raises(CheckFailure):
        await cmd.invoke(ctx)
