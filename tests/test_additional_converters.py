import pytest

from disagreement.ext.commands.converters import run_converters
from disagreement.ext.commands.core import CommandContext, Command
from disagreement.ext.commands.errors import BadArgument
from disagreement.models import (
    Message,
    Member,
    Role,
    Guild,
    User,
    TextChannel,
    VoiceChannel,
    PartialEmoji,
)
from disagreement.enums import (
    VerificationLevel,
    MessageNotificationLevel,
    ExplicitContentFilterLevel,
    MFALevel,
    GuildNSFWLevel,
    PremiumTier,
    ChannelType,
)


from disagreement.client import Client
from disagreement.cache import GuildCache, Cache, ChannelCache


class DummyBot(Client):
    def __init__(self):
        super().__init__(token="test")
        self._guilds = GuildCache()
        self._users = Cache()
        self._channels = ChannelCache()

    def get_guild(self, guild_id):
        return self._guilds.get(guild_id)

    def get_channel(self, channel_id):
        return self._channels.get(channel_id)

    async def fetch_member(self, guild_id, member_id):
        guild = self._guilds.get(guild_id)
        return guild.get_member(member_id) if guild else None

    async def fetch_role(self, guild_id, role_id):
        guild = self._guilds.get(guild_id)
        return guild.get_role(role_id) if guild else None

    async def fetch_guild(self, guild_id):
        return self._guilds.get(guild_id)

    async def fetch_user(self, user_id):
        return self._users.get(user_id)

    async def fetch_channel(self, channel_id):
        return self._channels.get(channel_id)


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

    user = User({"id": "7", "username": "u", "discriminator": "0001"})
    bot._users.set(user.id, user)

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

    text_channel = TextChannel(
        {
            "id": "20",
            "type": ChannelType.GUILD_TEXT.value,
            "guild_id": guild.id,
            "permission_overwrites": [],
        },
        client_instance=bot,
    )
    voice_channel = VoiceChannel(
        {
            "id": "21",
            "type": ChannelType.GUILD_VOICE.value,
            "guild_id": guild.id,
            "permission_overwrites": [],
        },
        client_instance=bot,
    )

    guild._channels.set(text_channel.id, text_channel)
    guild.text_channels.append(text_channel)
    guild._channels.set(voice_channel.id, voice_channel)
    guild.voice_channels.append(voice_channel)
    bot._channels.set(text_channel.id, text_channel)
    bot._channels.set(voice_channel.id, voice_channel)

    return guild, member, role, user, text_channel, voice_channel


@pytest.fixture()
def command_context(guild_objects):
    guild, member, role, _, _, _ = guild_objects
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
    _, member, _, _, _, _ = guild_objects
    mention = f"<@!{member.id}>"
    result = await run_converters(command_context, Member, mention)
    assert result is member
    result = await run_converters(command_context, Member, member.id)
    assert result is member


@pytest.mark.asyncio
async def test_role_converter(command_context, guild_objects):
    _, _, role, _, _, _ = guild_objects
    mention = f"<@&{role.id}>"
    result = await run_converters(command_context, Role, mention)
    assert result is role
    result = await run_converters(command_context, Role, role.id)
    assert result is role


@pytest.mark.asyncio
async def test_user_converter(command_context, guild_objects):
    _, _, _, user, _, _ = guild_objects
    mention = f"<@{user.id}>"
    result = await run_converters(command_context, User, mention)
    assert result is user
    result = await run_converters(command_context, User, user.id)
    assert result is user


@pytest.mark.asyncio
async def test_guild_converter(command_context, guild_objects):
    guild, _, _, _, _, _ = guild_objects
    result = await run_converters(command_context, Guild, guild.id)
    assert result is guild


@pytest.mark.asyncio
async def test_text_channel_converter(command_context, guild_objects):
    _, _, _, _, text_channel, _ = guild_objects
    mention = f"<#{text_channel.id}>"
    result = await run_converters(command_context, TextChannel, mention)
    assert result is text_channel
    result = await run_converters(command_context, TextChannel, text_channel.id)
    assert result is text_channel


@pytest.mark.asyncio
async def test_voice_channel_converter(command_context, guild_objects):
    _, _, _, _, _, voice_channel = guild_objects
    mention = f"<#{voice_channel.id}>"
    result = await run_converters(command_context, VoiceChannel, mention)
    assert result is voice_channel
    result = await run_converters(command_context, VoiceChannel, voice_channel.id)
    assert result is voice_channel


@pytest.mark.asyncio
async def test_emoji_converter(command_context):
    result = await run_converters(command_context, PartialEmoji, "<:smile:1>")
    assert isinstance(result, PartialEmoji)
    assert result.id == "1"
    assert result.name == "smile"

    result = await run_converters(command_context, PartialEmoji, "😄")
    assert result.id is None
    assert result.name == "😄"


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
