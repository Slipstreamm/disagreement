"""Utility helpers for working with Discord permission bitmasks."""

from __future__ import annotations

from enum import IntFlag
from typing import Iterable, List


class Permissions(IntFlag):
    """Discord guild and channel permissions."""

    CREATE_INSTANT_INVITE = 1 << 0
    KICK_MEMBERS = 1 << 1
    BAN_MEMBERS = 1 << 2
    ADMINISTRATOR = 1 << 3
    MANAGE_CHANNELS = 1 << 4
    MANAGE_GUILD = 1 << 5
    ADD_REACTIONS = 1 << 6
    VIEW_AUDIT_LOG = 1 << 7
    PRIORITY_SPEAKER = 1 << 8
    STREAM = 1 << 9
    VIEW_CHANNEL = 1 << 10
    SEND_MESSAGES = 1 << 11
    SEND_TTS_MESSAGES = 1 << 12
    MANAGE_MESSAGES = 1 << 13
    EMBED_LINKS = 1 << 14
    ATTACH_FILES = 1 << 15
    READ_MESSAGE_HISTORY = 1 << 16
    MENTION_EVERYONE = 1 << 17
    USE_EXTERNAL_EMOJIS = 1 << 18
    VIEW_GUILD_INSIGHTS = 1 << 19
    CONNECT = 1 << 20
    SPEAK = 1 << 21
    MUTE_MEMBERS = 1 << 22
    DEAFEN_MEMBERS = 1 << 23
    MOVE_MEMBERS = 1 << 24
    USE_VAD = 1 << 25
    CHANGE_NICKNAME = 1 << 26
    MANAGE_NICKNAMES = 1 << 27
    MANAGE_ROLES = 1 << 28
    MANAGE_WEBHOOKS = 1 << 29
    MANAGE_GUILD_EXPRESSIONS = 1 << 30
    USE_APPLICATION_COMMANDS = 1 << 31
    REQUEST_TO_SPEAK = 1 << 32
    MANAGE_EVENTS = 1 << 33
    MANAGE_THREADS = 1 << 34
    CREATE_PUBLIC_THREADS = 1 << 35
    CREATE_PRIVATE_THREADS = 1 << 36
    USE_EXTERNAL_STICKERS = 1 << 37
    SEND_MESSAGES_IN_THREADS = 1 << 38
    USE_EMBEDDED_ACTIVITIES = 1 << 39
    MODERATE_MEMBERS = 1 << 40
    VIEW_CREATOR_MONETIZATION_ANALYTICS = 1 << 41
    USE_SOUNDBOARD = 1 << 42
    CREATE_GUILD_EXPRESSIONS = 1 << 43
    CREATE_EVENTS = 1 << 44
    USE_EXTERNAL_SOUNDS = 1 << 45
    SEND_VOICE_MESSAGES = 1 << 46


def permissions_value(*perms: Permissions | int | Iterable[Permissions | int]) -> int:
    """Return a combined integer value for multiple permissions."""

    value = 0
    for perm in perms:
        if isinstance(perm, Iterable) and not isinstance(perm, (Permissions, int)):
            value |= permissions_value(*perm)
        else:
            value |= int(perm)
    return value


def has_permissions(
    current: int | str | Permissions,
    *perms: Permissions | int | Iterable[Permissions | int],
) -> bool:
    """Return ``True`` if ``current`` includes all ``perms``."""

    current_val = int(current)
    needed = permissions_value(*perms)
    return (current_val & needed) == needed


def missing_permissions(
    current: int | str | Permissions,
    *perms: Permissions | int | Iterable[Permissions | int],
) -> List[Permissions]:
    """Return the subset of ``perms`` not present in ``current``."""

    current_val = int(current)
    missing: List[Permissions] = []
    for perm in perms:
        if isinstance(perm, Iterable) and not isinstance(perm, (Permissions, int)):
            missing.extend(missing_permissions(current_val, *perm))
        else:
            perm_val = int(perm)
            if not current_val & perm_val:
                missing.append(Permissions(perm_val))
    return missing
