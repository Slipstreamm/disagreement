import time

from disagreement.cache import Cache
from disagreement.client import Client
from disagreement.caching import MemberCacheFlags
from disagreement.enums import (
    ChannelType,
    ExplicitContentFilterLevel,
    GuildNSFWLevel,
    MFALevel,
    MessageNotificationLevel,
    PremiumTier,
    VerificationLevel,
)


def _guild_payload(gid: str, channel_count: int, member_count: int) -> dict:
    base = {
        "id": gid,
        "name": f"g{gid}",
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
        "channels": [],
        "members": [],
    }
    for i in range(channel_count):
        base["channels"].append(
            {
                "id": f"{gid}-c{i}",
                "type": ChannelType.GUILD_TEXT.value,
                "guild_id": gid,
                "permission_overwrites": [],
            }
        )
    for i in range(member_count):
        base["members"].append(
            {
                "user": {
                    "id": f"{gid}-m{i}",
                    "username": f"u{i}",
                    "discriminator": "0001",
                },
                "joined_at": "t",
                "roles": [],
            }
        )
    return base


def test_cache_store_and_get():
    cache = Cache()
    cache.set("a", 123)
    assert cache.get("a") == 123


def test_cache_ttl_expiry():
    cache = Cache(ttl=0.01)
    cache.set("b", 1)
    assert cache.get("b") == 1
    time.sleep(0.02)
    assert cache.get("b") is None


def test_cache_lru_eviction():
    cache = Cache(maxlen=2)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1
    cache.set("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_get_or_fetch_uses_cache():
    cache = Cache()
    cache.set("a", 1)

    def fetch():
        raise AssertionError("fetch should not be called")

    assert cache.get_or_fetch("a", fetch) == 1


def test_get_or_fetch_fetches_and_stores():
    cache = Cache()
    called = False

    def fetch():
        nonlocal called
        called = True
        return 2

    assert cache.get_or_fetch("b", fetch) == 2
    assert called
    assert cache.get("b") == 2


def test_get_or_fetch_fetches_expired_item():
    cache = Cache(ttl=0.01)
    cache.set("c", 1)
    time.sleep(0.02)
    called = False

    def fetch():
        nonlocal called
        called = True
        return 3

    assert cache.get_or_fetch("c", fetch) == 3
    assert called


def test_client_get_all_channels_and_members():
    client = Client(token="t")
    client.parse_guild(_guild_payload("1", 2, 2))
    client.parse_guild(_guild_payload("2", 1, 1))

    channels = {c.id for c in client.get_all_channels()}
    members = {m.id for m in client.get_all_members()}

    assert channels == {"1-c0", "1-c1", "2-c0"}
    assert members == {"1-m0", "1-m1", "2-m0"}


def test_client_get_all_members_disabled_cache():
    client = Client(token="t", member_cache_flags=MemberCacheFlags.none())
    client.parse_guild(_guild_payload("1", 1, 2))

    assert client.get_all_members() == []
