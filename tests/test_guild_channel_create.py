import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.http import HTTPClient
from disagreement.client import Client
from disagreement.models import Guild, TextChannel, VoiceChannel, CategoryChannel
from disagreement.enums import (
    VerificationLevel,
    MessageNotificationLevel,
    ExplicitContentFilterLevel,
    MFALevel,
    GuildNSFWLevel,
    PremiumTier,
    ChannelType,
)


def _guild_data():
    return {
        "id": "1",
        "name": "g",
        "owner_id": "1",
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


@pytest.mark.asyncio
async def test_http_create_guild_channel_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={})
    payload = {"name": "chan", "type": ChannelType.GUILD_TEXT.value}

    await http.create_guild_channel("1", payload, reason="r")

    http.request.assert_called_once_with(
        "POST",
        "/guilds/1/channels",
        payload=payload,
        custom_headers={"X-Audit-Log-Reason": "r"},
    )


@pytest.mark.asyncio
async def test_guild_create_text_channel_returns_channel():
    http = SimpleNamespace(
        create_guild_channel=AsyncMock(
            return_value={
                "id": "10",
                "type": ChannelType.GUILD_TEXT.value,
                "guild_id": "1",
                "permission_overwrites": [],
            }
        )
    )
    client = Client(token="t")
    client._http = http
    guild = Guild(_guild_data(), client_instance=client)

    channel = await guild.create_text_channel("general")

    http.create_guild_channel.assert_awaited_once_with(
        "1", {"name": "general", "type": ChannelType.GUILD_TEXT.value}, reason=None
    )
    assert isinstance(channel, TextChannel)
    assert client._channels.get("10") is channel


@pytest.mark.asyncio
async def test_guild_create_voice_channel_returns_channel():
    http = SimpleNamespace(
        create_guild_channel=AsyncMock(
            return_value={
                "id": "11",
                "type": ChannelType.GUILD_VOICE.value,
                "guild_id": "1",
                "permission_overwrites": [],
            }
        )
    )
    client = Client(token="t")
    client._http = http
    guild = Guild(_guild_data(), client_instance=client)

    channel = await guild.create_voice_channel("Voice")

    http.create_guild_channel.assert_awaited_once_with(
        "1", {"name": "Voice", "type": ChannelType.GUILD_VOICE.value}, reason=None
    )
    assert isinstance(channel, VoiceChannel)
    assert client._channels.get("11") is channel


@pytest.mark.asyncio
async def test_guild_create_category_returns_channel():
    http = SimpleNamespace(
        create_guild_channel=AsyncMock(
            return_value={
                "id": "12",
                "type": ChannelType.GUILD_CATEGORY.value,
                "guild_id": "1",
                "permission_overwrites": [],
            }
        )
    )
    client = Client(token="t")
    client._http = http
    guild = Guild(_guild_data(), client_instance=client)

    channel = await guild.create_category("Cat")

    http.create_guild_channel.assert_awaited_once_with(
        "1", {"name": "Cat", "type": ChannelType.GUILD_CATEGORY.value}, reason=None
    )
    assert isinstance(channel, CategoryChannel)
    assert client._channels.get("12") is channel
