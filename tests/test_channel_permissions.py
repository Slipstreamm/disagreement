import pytest  # pylint: disable=E0401

from disagreement.models import Guild, Member, Role, TextChannel, PermissionOverwrite
from disagreement.enums import (
    ChannelType,
    VerificationLevel,
    MessageNotificationLevel,
    ExplicitContentFilterLevel,
    MFALevel,
    GuildNSFWLevel,
    PremiumTier,
    OverwriteType,
)
from disagreement.permissions import Permissions


class DummyClient:
    def __init__(self):
        self._guilds = {}

    def get_guild(self, gid):
        return self._guilds.get(gid)


def _base_guild(client):
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
    client._guilds[guild.id] = guild
    return guild


def _member(guild, *roles):
    data = {
        "user": {"id": "10", "username": "u", "discriminator": "0001"},
        "joined_at": "t",
        "roles": [r.id for r in roles] or [guild.id],
    }
    member = Member(data, client_instance=None)
    member.guild_id = guild.id
    guild._members[member.id] = member
    return member


def _role(guild, rid, perms):
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


def _channel(guild, client):
    data = {
        "id": "100",
        "type": ChannelType.GUILD_TEXT.value,
        "guild_id": guild.id,
        "permission_overwrites": [],
    }
    channel = TextChannel(data, client_instance=client)
    guild._channels[channel.id] = channel
    return channel


def test_permissions_for_base_roles():
    client = DummyClient()
    guild = _base_guild(client)
    everyone = _role(
        guild, guild.id, Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES
    )
    mod = _role(guild, "2", Permissions.MANAGE_MESSAGES)
    member = _member(guild, everyone, mod)
    channel = _channel(guild, client)

    perms = channel.permissions_for(member)
    assert perms & Permissions.MANAGE_MESSAGES
    assert perms & Permissions.SEND_MESSAGES
    assert perms & Permissions.VIEW_CHANNEL


def test_permissions_for_with_overwrite():
    client = DummyClient()
    guild = _base_guild(client)
    everyone = _role(
        guild, guild.id, Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES
    )
    mod = _role(guild, "2", Permissions.MANAGE_MESSAGES)
    member = _member(guild, everyone, mod)
    channel = _channel(guild, client)

    channel.permission_overwrites.append(
        PermissionOverwrite(
            {
                "id": mod.id,
                "type": OverwriteType.ROLE.value,
                "allow": "0",
                "deny": str(int(Permissions.MANAGE_MESSAGES)),
            }
        )
    )

    perms = channel.permissions_for(member)
    assert not perms & Permissions.MANAGE_MESSAGES
    assert perms & Permissions.SEND_MESSAGES
    assert perms & Permissions.VIEW_CHANNEL
