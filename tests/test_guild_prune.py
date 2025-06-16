import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.http import HTTPClient
from disagreement.client import Client
from disagreement.enums import (
    VerificationLevel,
    MessageNotificationLevel,
    ExplicitContentFilterLevel,
    MFALevel,
    GuildNSFWLevel,
    PremiumTier,
)
from disagreement.models import Guild


@pytest.mark.asyncio
async def test_http_get_guild_prune_count_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={"pruned": 3})
    count = await http.get_guild_prune_count("1", days=7)
    http.request.assert_called_once_with("GET", f"/guilds/1/prune", params={"days": 7})
    assert count == 3


@pytest.mark.asyncio
async def test_http_begin_guild_prune_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={"pruned": 2})
    count = await http.begin_guild_prune("1", days=1, compute_count=True)
    http.request.assert_called_once_with(
        "POST",
        f"/guilds/1/prune",
        payload={"days": 1, "compute_prune_count": True},
    )
    assert count == 2


@pytest.mark.asyncio
async def test_guild_prune_members_calls_http():
    http = SimpleNamespace(begin_guild_prune=AsyncMock(return_value=1))
    client = Client(token="t")
    client._http = http
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
    }
    guild = Guild(guild_data, client_instance=client)
    count = await guild.prune_members(2)
    http.begin_guild_prune.assert_awaited_once_with("1", days=2, compute_count=True)
    assert count == 1
