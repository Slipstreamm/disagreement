import asyncio
import pytest

from disagreement.ext.commands.core import Command, CommandContext
from disagreement.ext.commands.decorators import check, cooldown
from disagreement.ext.commands.errors import CheckFailure, CommandOnCooldown


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

    @cooldown(1, 0.05)
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

    await asyncio.sleep(0.05)
    await cmd.invoke(ctx)
    assert len(uses) == 2
