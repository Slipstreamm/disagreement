import types
from disagreement.models import User, Guild, Channel, Message
from disagreement.enums import (
    VerificationLevel,
    MessageNotificationLevel,
    ExplicitContentFilterLevel,
    MFALevel,
    GuildNSFWLevel,
    PremiumTier,
    ChannelType,
)


def _guild_data(gid="1"):
    return {
        "id": gid,
        "name": "g",
        "owner_id": gid,
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


def _user(uid="1"):
    return User({"id": uid, "username": "u", "discriminator": "0001"})


def _message(mid="1"):
    data = {
        "id": mid,
        "channel_id": "c",
        "author": {"id": "2", "username": "u", "discriminator": "0001"},
        "content": "hi",
        "timestamp": "t",
    }
    return Message(data, client_instance=types.SimpleNamespace())


def _channel(cid="1"):
    data = {"id": cid, "type": ChannelType.GUILD_TEXT.value}
    return Channel(data, client_instance=types.SimpleNamespace())


def test_user_hash_and_eq():
    a = _user()
    b = _user()
    c = _user("2")
    assert a == b
    assert hash(a) == hash(b)
    assert a != c


def test_guild_hash_and_eq():
    a = Guild(_guild_data(), client_instance=types.SimpleNamespace())
    b = Guild(_guild_data(), client_instance=types.SimpleNamespace())
    c = Guild(_guild_data("2"), client_instance=types.SimpleNamespace())
    assert a == b
    assert hash(a) == hash(b)
    assert a != c


def test_channel_hash_and_eq():
    a = _channel()
    b = _channel()
    c = _channel("2")
    assert a == b
    assert hash(a) == hash(b)
    assert a != c


def test_message_hash_and_eq():
    a = _message()
    b = _message()
    c = _message("2")
    assert a == b
    assert hash(a) == hash(b)
    assert a != c
