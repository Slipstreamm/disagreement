import pytest  # pylint: disable=E0401

from disagreement.client import Client
from disagreement.enums import (
    VerificationLevel,
    MessageNotificationLevel,
    ExplicitContentFilterLevel,
    MFALevel,
    GuildNSFWLevel,
    PremiumTier,
)
from disagreement.models import Member, Guild, Role
from disagreement.permissions import Permissions


class DummyClient(Client):
    def __init__(self):
        super().__init__(token="test")


def _make_member(member_id: str, username: str, nick: str | None):
    data = {
        "user": {"id": member_id, "username": username, "discriminator": "0001"},
        "joined_at": "t",
        "roles": [],
    }
    if nick is not None:
        data["nick"] = nick
    return Member(data, client_instance=None)


def _base_guild(client: Client) -> Guild:
    data = {
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
    guild = Guild(data, client_instance=client)
    client._guilds.set(guild.id, guild)
    return guild


def _role(guild: Guild, rid: str, perms: Permissions) -> Role:
    role = Role(
        {
            "id": rid,
            "name": f"r{rid}",
            "color": 0,
            "hoist": False,
            "position": 0,
            "permissions": str(int(perms)),
            "managed": False,
            "mentionable": False,
        }
    )
    guild.roles.append(role)
    return role


def _member(guild: Guild, client: Client, *roles: Role) -> Member:
    data = {
        "user": {"id": "10", "username": "u", "discriminator": "0001"},
        "joined_at": "t",
        "roles": [r.id for r in roles] or [guild.id],
    }
    member = Member(data, client_instance=client)
    member.guild_id = guild.id
    member._client = client
    guild._members.set(member.id, member)
    return member


def test_display_name_prefers_nick():
    member = _make_member("1", "u", "nickname")
    assert member.display_name == "nickname"


def test_display_name_falls_back_to_username():
    member = _make_member("2", "u2", None)
    assert member.display_name == "u2"


def test_guild_permissions_from_roles():
    client = DummyClient()
    guild = _base_guild(client)
    everyone = _role(guild, guild.id, Permissions.VIEW_CHANNEL)
    mod = _role(guild, "2", Permissions.MANAGE_MESSAGES)
    member = _member(guild, client, everyone, mod)

    perms = member.guild_permissions
    assert perms & Permissions.VIEW_CHANNEL
    assert perms & Permissions.MANAGE_MESSAGES
    assert not perms & Permissions.BAN_MEMBERS


def test_guild_permissions_administrator_role_grants_all():
    client = DummyClient()
    guild = _base_guild(client)
    admin = _role(guild, "2", Permissions.ADMINISTRATOR)
    member = _member(guild, client, admin)

    assert member.guild_permissions == Permissions(~0)
