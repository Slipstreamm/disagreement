import pytest
from unittest.mock import Mock

from disagreement.models import Guild
from disagreement.enums import (
    VerificationLevel,
    MessageNotificationLevel,
    ExplicitContentFilterLevel,
    MFALevel,
    GuildNSFWLevel,
    PremiumTier,
)


class DummyShard:
    def __init__(self, shard_id):
        self.id = shard_id
        self.count = 1
        self.gateway = Mock()


class DummyManager:
    def __init__(self):
        self.shards = [DummyShard(0)]


class DummyClient:
    pass


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
        "shard_id": 0,
    }


def test_guild_shard_property():
    client = DummyClient()
    client._shard_manager = DummyManager()
    guild = Guild(_guild_data(), client_instance=client, shard_id=0)
    assert guild.shard_id == 0
    assert guild.shard is client._shard_manager.shards[0]
