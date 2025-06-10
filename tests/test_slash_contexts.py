import pytest

from disagreement.ext.app_commands.decorators import slash_command
from disagreement.ext.app_commands.commands import SlashCommand
from disagreement.enums import InteractionContextType


async def dummy(ctx):
    pass


def test_boolean_context_parameters():
    cmd = slash_command(description="test", dms=False, private_channels=False)(dummy)
    assert isinstance(cmd, SlashCommand)
    assert cmd.contexts == [InteractionContextType.GUILD]
