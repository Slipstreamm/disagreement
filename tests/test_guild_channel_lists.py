import pytest

from disagreement.client import Client
from disagreement.enums import (
    ChannelType,
    VerificationLevel,
    MessageNotificationLevel,
    ExplicitContentFilterLevel,
    MFALevel,
    GuildNSFWLevel,
    PremiumTier,
)
from disagreement.models import TextChannel, VoiceChannel, CategoryChannel


@pytest.mark.asyncio
async def test_guild_channel_lists_populated():
    client = Client(token="t")
    guild_data = {
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
        "channels": [
            {
                "id": "10",
                "type": ChannelType.GUILD_TEXT.value,
                "guild_id": "1",
                "permission_overwrites": [],
            },
            {
                "id": "11",
                "type": ChannelType.GUILD_VOICE.value,
                "guild_id": "1",
                "permission_overwrites": [],
            },
            {
                "id": "12",
                "type": ChannelType.GUILD_CATEGORY.value,
                "guild_id": "1",
                "permission_overwrites": [],
            },
        ],
    }

    guild = client.parse_guild(guild_data)

    assert len(guild.text_channels) == 1
    assert isinstance(guild.text_channels[0], TextChannel)
    assert len(guild.voice_channels) == 1
    assert isinstance(guild.voice_channels[0], VoiceChannel)
    assert len(guild.category_channels) == 1
    assert isinstance(guild.category_channels[0], CategoryChannel)
