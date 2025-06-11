import pytest

from disagreement.ext.commands.converters import run_converters
from disagreement.ext.commands.core import CommandContext, Command
from disagreement.ext.commands.errors import BadArgument
from disagreement.models import Message, Member, Role, Guild
from disagreement.enums import (
    VerificationLevel,
    MessageNotificationLevel,
    ExplicitContentFilterLevel,
    MFALevel,
    GuildNSFWLevel,
    PremiumTier,
)


from disagreement.client import Client
from disagreement.cache import GuildCache


class DummyBot(Client):
    def __init__(self):
        super().__init__(token="test")
        self._guilds = GuildCache()

    def get_guild(self, guild_id):
        return self._guilds.get(guild_id)

    async def fetch_member(self, guild_id, member_id):
        guild = self._guilds.get(guild_id)
        return guild.get_member(member_id) if guild else None

    async def fetch_role(self, guild_id, role_id):
        guild = self._guilds.get(guild_id)
        return guild.get_role(role_id) if guild else None

    async def fetch_guild(self, guild_id):
        return self._guilds.get(guild_id)


@pytest.fixture()
def guild_objects():
    guild_data = {
        "id": "1",
        "name": "g",
        "owner_id": "2",
        "afk_timeout": 60,
        "verification_level": VerificationLevel.NONE.value,
        "default_message_notifications": MessageNotificationLevel.ALL_MESSAGES.value,
        "explicit_content_filter": ExplicitContentFilterLevel.DISABLED.value,
        "roles": [],
        "emojis": [],
        "features": [],
        "mfa_level": MFALevel.NONE.value,
        "system_channel_flags": 0,
        "premium_tier": PremiumTier.NONE.value,
        "nsfw_level": GuildNSFWLevel.DEFAULT.value,
    }
    bot = DummyBot()
    guild = Guild(guild_data, client_instance=bot)
    bot._guilds.set(guild.id, guild)

    member = Member(
        {
            "user": {"id": "3", "username": "m", "discriminator": "0001"},
            "joined_at": "t",
            "roles": [],
        },
        None,
    )
    member.guild_id = guild.id

    role = Role(
        {
            "id": "5",
            "name": "r",
            "color": 0,
            "hoist": False,
            "position": 0,
            "permissions": "0",
            "managed": False,
            "mentionable": True,
        }
    )

    guild._members.set(member.id, member)
    guild.roles.append(role)

    return guild, member, role


@pytest.fixture()
def command_context(guild_objects):
    guild, member, role = guild_objects
    bot = guild._client
    message_data = {
        "id": "10",
        "channel_id": "20",
        "guild_id": guild.id,
        "author": {"id": "2", "username": "u", "discriminator": "0001"},
        "content": "hi",
        "timestamp": "t",
    }
    msg = Message(message_data, client_instance=bot)

    async def dummy(ctx):
        pass

    cmd = Command(dummy)
    return CommandContext(
        message=msg, bot=bot, prefix="!", command=cmd, invoked_with="dummy"
    )


@pytest.mark.asyncio
async def test_member_converter(command_context, guild_objects):
    _, member, _ = guild_objects
    mention = f"<@!{member.id}>"
    result = await run_converters(command_context, Member, mention)
    assert result is member
    result = await run_converters(command_context, Member, member.id)
    assert result is member


@pytest.mark.asyncio
async def test_role_converter(command_context, guild_objects):
    _, _, role = guild_objects
    mention = f"<@&{role.id}>"
    result = await run_converters(command_context, Role, mention)
    assert result is role
    result = await run_converters(command_context, Role, role.id)
    assert result is role


@pytest.mark.asyncio
async def test_guild_converter(command_context, guild_objects):
    guild, _, _ = guild_objects
    result = await run_converters(command_context, Guild, guild.id)
    assert result is guild


@pytest.mark.asyncio
async def test_member_converter_no_guild():
    guild_data = {
        "id": "99",
        "name": "g",
        "owner_id": "2",
        "afk_timeout": 60,
        "verification_level": VerificationLevel.NONE.value,
        "default_message_notifications": MessageNotificationLevel.ALL_MESSAGES.value,
        "explicit_content_filter": ExplicitContentFilterLevel.DISABLED.value,
        "roles": [],
        "emojis": [],
        "features": [],
        "mfa_level": MFALevel.NONE.value,
        "system_channel_flags": 0,
        "premium_tier": PremiumTier.NONE.value,
        "nsfw_level": GuildNSFWLevel.DEFAULT.value,
    }
    bot = DummyBot()
    guild = Guild(guild_data, client_instance=bot)
    bot._guilds.set(guild.id, guild)
    message_data = {
        "id": "11",
        "channel_id": "20",
        "author": {"id": "2", "username": "u", "discriminator": "0001"},
        "content": "hi",
        "timestamp": "t",
    }
    msg = Message(message_data, client_instance=bot)

    async def dummy(ctx):
        pass

    ctx = CommandContext(
        message=msg, bot=bot, prefix="!", command=Command(dummy), invoked_with="dummy"
    )

    with pytest.raises(BadArgument):
        await run_converters(ctx, Member, "<@!1>")
