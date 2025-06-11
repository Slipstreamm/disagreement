# disagreement/models.py

"""
Data models for Discord objects.
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, TYPE_CHECKING, Union

import aiohttp  # pylint: disable=import-error
from .color import Color
from .errors import DisagreementException, HTTPException
from .enums import (  # These enums will need to be defined in disagreement/enums.py
    VerificationLevel,
    MessageNotificationLevel,
    ExplicitContentFilterLevel,
    MFALevel,
    GuildNSFWLevel,
    PremiumTier,
    GuildFeature,
    ChannelType,
    ComponentType,
    ButtonStyle,  # Added for Button
    GuildScheduledEventPrivacyLevel,
    GuildScheduledEventStatus,
    GuildScheduledEventEntityType,
    # SelectMenuType will be part of ComponentType or a new enum if needed
)
from .permissions import Permissions


if TYPE_CHECKING:
    from .client import Client  # For type hinting to avoid circular imports
    from .enums import OverwriteType  # For PermissionOverwrite model
    from .ui.view import View
    from .interactions import Snowflake

    # Forward reference Message if it were used in type hints before its definition
    # from .models import Message # Not needed as Message is defined before its use in TextChannel.send etc.
    from .components import component_factory


class User:
    """Represents a Discord User.

    Attributes:
        id (str): The user's unique ID.
        username (str): The user's username.
        discriminator (str): The user's 4-digit discord-tag.
        bot (bool): Whether the user belongs to an OAuth2 application. Defaults to False.
        avatar (Optional[str]): The user's avatar hash, if any.
    """

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.username: str = data["username"]
        self.discriminator: str = data["discriminator"]
        self.bot: bool = data.get("bot", False)
        self.avatar: Optional[str] = data.get("avatar")

    @property
    def mention(self) -> str:
        """str: Returns a string that allows you to mention the user."""
        return f"<@{self.id}>"

    def __repr__(self) -> str:
        return f"<User id='{self.id}' username='{self.username}' discriminator='{self.discriminator}'>"


class Message:
    """Represents a message sent in a channel on Discord.

    Attributes:
        id (str): The message's unique ID.
        channel_id (str): The ID of the channel the message was sent in.
        guild_id (Optional[str]): The ID of the guild the message was sent in, if applicable.
        author (User): The user who sent the message.
        content (str): The actual content of the message.
        timestamp (str): When this message was sent (ISO8601 timestamp).
        components (Optional[List[ActionRow]]): Structured components attached
            to the message if present.
        attachments (List[Attachment]): Attachments included with the message.
    """

    def __init__(self, data: dict, client_instance: "Client"):
        self._client: "Client" = (
            client_instance  # Store reference to client for methods like reply
        )

        self.id: str = data["id"]
        self.channel_id: str = data["channel_id"]
        self.guild_id: Optional[str] = data.get("guild_id")
        self.author: User = User(data["author"])
        self.content: str = data["content"]
        self.timestamp: str = data["timestamp"]
        if data.get("components"):
            self.components: Optional[List[ActionRow]] = [
                ActionRow.from_dict(c, client_instance)
                for c in data.get("components", [])
            ]
        else:
            self.components = None
        self.attachments: List[Attachment] = [
            Attachment(a) for a in data.get("attachments", [])
        ]
        # Add other fields as needed, e.g., attachments, embeds, reactions, etc.
        # self.mentions: List[User] = [User(u) for u in data.get("mentions", [])]
        # self.mention_roles: List[str] = data.get("mention_roles", [])
        # self.mention_everyone: bool = data.get("mention_everyone", False)

    async def reply(
        self,
        content: Optional[str] = None,
        *,  # Make additional params keyword-only
        tts: bool = False,
        embed: Optional["Embed"] = None,
        embeds: Optional[List["Embed"]] = None,
        components: Optional[List["ActionRow"]] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
        mention_author: Optional[bool] = None,
        flags: Optional[int] = None,
        view: Optional["View"] = None,
    ) -> "Message":
        """|coro|

        Sends a reply to the message.
        This is a shorthand for `Client.send_message` in the message's channel.

        Parameters:
            content (Optional[str]): The content of the message.
            tts (bool): Whether the message should be sent with text-to-speech.
            embed (Optional[Embed]): A single embed to send. Cannot be used with `embeds`.
            embeds (Optional[List[Embed]]): A list of embeds to send.
            components (Optional[List[ActionRow]]): A list of ActionRow components.
            allowed_mentions (Optional[Dict[str, Any]]): Allowed mentions for the message.
            mention_author (Optional[bool]): Whether to mention the author in the reply. If ``None`` the
                client's :attr:`mention_replies` setting is used.
            flags (Optional[int]): Message flags.
            view (Optional[View]): A view to send with the message.

        Returns:
            Message: The message that was sent.

        Raises:
            HTTPException: Sending the message failed.
            ValueError: If both `embed` and `embeds` are provided.
        """
        # Determine allowed mentions for the reply
        if mention_author is None:
            mention_author = getattr(self._client, "mention_replies", False)

        if allowed_mentions is None:
            allowed_mentions = {"replied_user": mention_author}
        else:
            allowed_mentions = dict(allowed_mentions)
            allowed_mentions.setdefault("replied_user", mention_author)

        # Client.send_message is already updated to handle these parameters
        return await self._client.send_message(
            channel_id=self.channel_id,
            content=content,
            tts=tts,
            embed=embed,
            embeds=embeds,
            components=components,
            allowed_mentions=allowed_mentions,
            message_reference={
                "message_id": self.id,
                "channel_id": self.channel_id,
                "guild_id": self.guild_id,
            },
            flags=flags,
            view=view,
        )

    async def edit(
        self,
        *,
        content: Optional[str] = None,
        embed: Optional["Embed"] = None,
        embeds: Optional[List["Embed"]] = None,
        components: Optional[List["ActionRow"]] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
        flags: Optional[int] = None,
        view: Optional["View"] = None,
    ) -> "Message":
        """|coro|

        Edits this message.

        Parameters are the same as :meth:`Client.edit_message`.
        """

        return await self._client.edit_message(
            channel_id=self.channel_id,
            message_id=self.id,
            content=content,
            embed=embed,
            embeds=embeds,
            components=components,
            allowed_mentions=allowed_mentions,
            flags=flags,
            view=view,
        )

    async def add_reaction(self, emoji: str) -> None:
        """|coro| Add a reaction to this message."""

        await self._client.add_reaction(self.channel_id, self.id, emoji)

    async def remove_reaction(self, emoji: str) -> None:
        """|coro| Remove the bot's reaction from this message."""

        await self._client.remove_reaction(self.channel_id, self.id, emoji)

    async def clear_reactions(self) -> None:
        """|coro| Remove all reactions from this message."""

        await self._client.clear_reactions(self.channel_id, self.id)

    async def delete(self, delay: Optional[float] = None) -> None:
        """|coro|

        Deletes this message.

        Parameters
        ----------
        delay:
            If provided, wait this many seconds before deleting.
        """

        if delay is not None:
            await asyncio.sleep(delay)

        await self._client._http.delete_message(self.channel_id, self.id)

    def __repr__(self) -> str:
        return f"<Message id='{self.id}' channel_id='{self.channel_id}' author='{self.author!r}'>"


class EmbedFooter:
    """Represents an embed footer."""

    def __init__(self, data: Dict[str, Any]):
        self.text: str = data["text"]
        self.icon_url: Optional[str] = data.get("icon_url")
        self.proxy_icon_url: Optional[str] = data.get("proxy_icon_url")

    def to_dict(self) -> Dict[str, Any]:
        payload = {"text": self.text}
        if self.icon_url:
            payload["icon_url"] = self.icon_url
        if self.proxy_icon_url:
            payload["proxy_icon_url"] = self.proxy_icon_url
        return payload


class EmbedImage:
    """Represents an embed image."""

    def __init__(self, data: Dict[str, Any]):
        self.url: str = data["url"]
        self.proxy_url: Optional[str] = data.get("proxy_url")
        self.height: Optional[int] = data.get("height")
        self.width: Optional[int] = data.get("width")

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"url": self.url}
        if self.proxy_url:
            payload["proxy_url"] = self.proxy_url
        if self.height:
            payload["height"] = self.height
        if self.width:
            payload["width"] = self.width
        return payload

    def __repr__(self) -> str:
        return f"<EmbedImage url='{self.url}'>"


class EmbedThumbnail(EmbedImage):  # Similar structure to EmbedImage
    """Represents an embed thumbnail."""

    pass


class EmbedAuthor:
    """Represents an embed author."""

    def __init__(self, data: Dict[str, Any]):
        self.name: str = data["name"]
        self.url: Optional[str] = data.get("url")
        self.icon_url: Optional[str] = data.get("icon_url")
        self.proxy_icon_url: Optional[str] = data.get("proxy_icon_url")

    def to_dict(self) -> Dict[str, Any]:
        payload = {"name": self.name}
        if self.url:
            payload["url"] = self.url
        if self.icon_url:
            payload["icon_url"] = self.icon_url
        if self.proxy_icon_url:
            payload["proxy_icon_url"] = self.proxy_icon_url
        return payload


class EmbedField:
    """Represents an embed field."""

    def __init__(self, data: Dict[str, Any]):
        self.name: str = data["name"]
        self.value: str = data["value"]
        self.inline: bool = data.get("inline", False)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value, "inline": self.inline}


class Embed:
    """Represents a Discord embed.

    Attributes can be set directly or via methods like `set_author`, `add_field`.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        data = data or {}
        self.title: Optional[str] = data.get("title")
        self.type: str = data.get("type", "rich")  # Default to "rich" for sending
        self.description: Optional[str] = data.get("description")
        self.url: Optional[str] = data.get("url")
        self.timestamp: Optional[str] = data.get("timestamp")  # ISO8601 timestamp
        self.color = Color.parse(data.get("color"))

        self.footer: Optional[EmbedFooter] = (
            EmbedFooter(data["footer"]) if data.get("footer") else None
        )
        self.image: Optional[EmbedImage] = (
            EmbedImage(data["image"]) if data.get("image") else None
        )
        self.thumbnail: Optional[EmbedThumbnail] = (
            EmbedThumbnail(data["thumbnail"]) if data.get("thumbnail") else None
        )
        # Video and Provider are less common for bot-sent embeds, can be added if needed.
        self.author: Optional[EmbedAuthor] = (
            EmbedAuthor(data["author"]) if data.get("author") else None
        )
        self.fields: List[EmbedField] = (
            [EmbedField(f) for f in data["fields"]] if data.get("fields") else []
        )

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"type": self.type}
        if self.title:
            payload["title"] = self.title
        if self.description:
            payload["description"] = self.description
        if self.url:
            payload["url"] = self.url
        if self.timestamp:
            payload["timestamp"] = self.timestamp
        if self.color is not None:
            payload["color"] = self.color.value
        if self.footer:
            payload["footer"] = self.footer.to_dict()
        if self.image:
            payload["image"] = self.image.to_dict()
        if self.thumbnail:
            payload["thumbnail"] = self.thumbnail.to_dict()
        if self.author:
            payload["author"] = self.author.to_dict()
        if self.fields:
            payload["fields"] = [f.to_dict() for f in self.fields]
        return payload

    # Convenience methods for building embeds can be added here
    # e.g., set_author, add_field, set_footer, set_image, etc.


class Attachment:
    """Represents a message attachment."""

    def __init__(self, data: Dict[str, Any]):
        self.id: str = data["id"]
        self.filename: str = data["filename"]
        self.description: Optional[str] = data.get("description")
        self.content_type: Optional[str] = data.get("content_type")
        self.size: Optional[int] = data.get("size")
        self.url: Optional[str] = data.get("url")
        self.proxy_url: Optional[str] = data.get("proxy_url")
        self.height: Optional[int] = data.get("height")  # If image
        self.width: Optional[int] = data.get("width")  # If image
        self.ephemeral: bool = data.get("ephemeral", False)

    def __repr__(self) -> str:
        return f"<Attachment id='{self.id}' filename='{self.filename}'>"

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"id": self.id, "filename": self.filename}
        if self.description is not None:
            payload["description"] = self.description
        if self.content_type is not None:
            payload["content_type"] = self.content_type
        if self.size is not None:
            payload["size"] = self.size
        if self.url is not None:
            payload["url"] = self.url
        if self.proxy_url is not None:
            payload["proxy_url"] = self.proxy_url
        if self.height is not None:
            payload["height"] = self.height
        if self.width is not None:
            payload["width"] = self.width
        if self.ephemeral:
            payload["ephemeral"] = self.ephemeral
        return payload


class File:
    """Represents a file to be uploaded."""

    def __init__(self, filename: str, data: bytes):
        self.filename = filename
        self.data = data


class AllowedMentions:
    """Represents allowed mentions for a message or interaction response."""

    def __init__(self, data: Dict[str, Any]):
        self.parse: List[str] = data.get("parse", [])
        self.roles: List[str] = data.get("roles", [])
        self.users: List[str] = data.get("users", [])
        self.replied_user: bool = data.get("replied_user", False)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"parse": self.parse}
        if self.roles:
            payload["roles"] = self.roles
        if self.users:
            payload["users"] = self.users
        if self.replied_user:
            payload["replied_user"] = self.replied_user
        return payload


class RoleTags:
    """Represents tags for a role."""

    def __init__(self, data: Dict[str, Any]):
        self.bot_id: Optional[str] = data.get("bot_id")
        self.integration_id: Optional[str] = data.get("integration_id")
        self.premium_subscriber: Optional[bool] = (
            data.get("premium_subscriber") is None
        )  # presence of null value means true

    def to_dict(self) -> Dict[str, Any]:
        payload = {}
        if self.bot_id:
            payload["bot_id"] = self.bot_id
        if self.integration_id:
            payload["integration_id"] = self.integration_id
        if self.premium_subscriber:
            payload["premium_subscriber"] = None  # Explicitly null
        return payload


class Role:
    """Represents a Discord Role."""

    def __init__(self, data: Dict[str, Any]):
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.color: int = data["color"]
        self.hoist: bool = data["hoist"]
        self.icon: Optional[str] = data.get("icon")
        self.unicode_emoji: Optional[str] = data.get("unicode_emoji")
        self.position: int = data["position"]
        self.permissions: str = data["permissions"]  # String of bitwise permissions
        self.managed: bool = data["managed"]
        self.mentionable: bool = data["mentionable"]
        self.tags: Optional[RoleTags] = (
            RoleTags(data["tags"]) if data.get("tags") else None
        )

    @property
    def mention(self) -> str:
        """str: Returns a string that allows you to mention the role."""
        return f"<@&{self.id}>"

    def __repr__(self) -> str:
        return f"<Role id='{self.id}' name='{self.name}'>"


class Member(User):  # Member inherits from User
    """Represents a Guild Member.
    This class combines User attributes with guild-specific Member attributes.
    """

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client: Optional["Client"] = client_instance
        self.guild_id: Optional[str] = None
        # User part is nested under 'user' key in member data from gateway/API
        user_data = data.get("user", {})
        # If 'id' is not in user_data but is top-level (e.g. from interaction resolved member without user object)
        if "id" not in user_data and "id" in data:
            # This case is less common for full member objects but can happen.
            # We'd need to construct a partial user from top-level member fields if 'user' is missing.
            # For now, assume 'user' object is present for full Member hydration.
            # If 'user' is missing, the User part might be incomplete.
            pass  # User fields will be missing or default if 'user' not in data.

        super().__init__(
            user_data if user_data else data
        )  # Pass user_data or data if user_data is empty

        self.nick: Optional[str] = data.get("nick")
        self.avatar: Optional[str] = data.get("avatar")  # Guild-specific avatar hash
        self.roles: List[str] = data.get("roles", [])  # List of role IDs
        self.joined_at: str = data["joined_at"]  # ISO8601 timestamp
        self.premium_since: Optional[str] = data.get(
            "premium_since"
        )  # ISO8601 timestamp
        self.deaf: bool = data.get("deaf", False)
        self.mute: bool = data.get("mute", False)
        self.pending: bool = data.get("pending", False)
        self.permissions: Optional[str] = data.get(
            "permissions"
        )  # Permissions in the channel, if applicable
        self.communication_disabled_until: Optional[str] = data.get(
            "communication_disabled_until"
        )  # ISO8601 timestamp

        # If 'user' object was present, ensure User attributes are from there
        if user_data:
            self.id = user_data.get("id", self.id)  # Prefer user.id if available
            self.username = user_data.get("username", self.username)
            self.discriminator = user_data.get("discriminator", self.discriminator)
            self.bot = user_data.get("bot", self.bot)
            # User's global avatar is User.avatar, Member.avatar is guild-specific
            # super() already set self.avatar from user_data if present.
            # The self.avatar = data.get("avatar") line above overwrites it with guild avatar. This is correct.

    def __repr__(self) -> str:
        return f"<Member id='{self.id}' username='{self.username}' nick='{self.nick}'>"

    @property
    def display_name(self) -> str:
        """Return the nickname if set, otherwise the username."""

        return self.nick or self.username

    async def kick(self, *, reason: Optional[str] = None) -> None:
        if not self.guild_id or not self._client:
            raise DisagreementException("Member.kick requires guild_id and client")
        await self._client._http.kick_member(self.guild_id, self.id, reason=reason)

    async def ban(
        self,
        *,
        delete_message_seconds: int = 0,
        reason: Optional[str] = None,
    ) -> None:
        if not self.guild_id or not self._client:
            raise DisagreementException("Member.ban requires guild_id and client")
        await self._client._http.ban_member(
            self.guild_id,
            self.id,
            delete_message_seconds=delete_message_seconds,
            reason=reason,
        )

    async def timeout(
        self, until: Optional[str], *, reason: Optional[str] = None
    ) -> None:
        if not self.guild_id or not self._client:
            raise DisagreementException("Member.timeout requires guild_id and client")
        await self._client._http.timeout_member(
            self.guild_id,
            self.id,
            until=until,
            reason=reason,
        )

    @property
    def top_role(self) -> Optional["Role"]:
        """Return the member's highest role from the guild cache."""

        if not self.guild_id or not self._client:
            return None

        guild = self._client.get_guild(self.guild_id)
        if not guild:
            return None

        if not guild.roles and hasattr(self._client, "fetch_roles"):
            try:
                self._client.loop.run_until_complete(
                    self._client.fetch_roles(self.guild_id)
                )
            except RuntimeError:
                future = asyncio.run_coroutine_threadsafe(
                    self._client.fetch_roles(self.guild_id), self._client.loop
                )
                future.result()

        role_objects = [r for r in guild.roles if r.id in self.roles]
        if not role_objects:
            return None

        return max(role_objects, key=lambda r: r.position)


class PartialEmoji:
    """Represents a partial emoji, often used in components or reactions.

    This typically means only id, name, and animated are known.
    For unicode emojis, id will be None and name will be the unicode character.
    """

    def __init__(self, data: Dict[str, Any]):
        self.id: Optional[str] = data.get("id")
        self.name: Optional[str] = data.get(
            "name"
        )  # Can be None for unknown custom emoji, or unicode char
        self.animated: bool = data.get("animated", False)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if self.id:
            payload["id"] = self.id
        if self.name:
            payload["name"] = self.name
        if self.animated:  # Only include if true, as per some Discord patterns
            payload["animated"] = self.animated
        return payload

    def __str__(self) -> str:
        if self.id:
            return f"<{'a' if self.animated else ''}:{self.name}:{self.id}>"
        return self.name or ""  # For unicode emoji

    def __repr__(self) -> str:
        return (
            f"<PartialEmoji id='{self.id}' name='{self.name}' animated={self.animated}>"
        )


def to_partial_emoji(
    value: Union[str, "PartialEmoji", None],
) -> Optional["PartialEmoji"]:
    """Convert a string or PartialEmoji to a PartialEmoji instance.

    Args:
        value: Either a unicode emoji string, a :class:`PartialEmoji`, or ``None``.

    Returns:
        A :class:`PartialEmoji` or ``None`` if ``value`` was ``None``.

    Raises:
        TypeError: If ``value`` is not ``str`` or :class:`PartialEmoji`.
    """

    if value is None or isinstance(value, PartialEmoji):
        return value
    if isinstance(value, str):
        return PartialEmoji({"name": value, "id": None})
    raise TypeError("emoji must be a str or PartialEmoji")


class Emoji(PartialEmoji):
    """Represents a custom guild emoji.

    Inherits id, name, animated from PartialEmoji.
    """

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        super().__init__(data)
        self._client: Optional["Client"] = (
            client_instance  # For potential future methods
        )

        # Roles this emoji is whitelisted to
        self.roles: List[str] = data.get("roles", [])  # List of role IDs

        # User object for the user that created this emoji (optional, only for GUILD_EMOJIS_AND_STICKERS intent)
        self.user: Optional[User] = User(data["user"]) if data.get("user") else None

        self.require_colons: bool = data.get("require_colons", False)
        self.managed: bool = data.get(
            "managed", False
        )  # If this emoji is managed by an integration
        self.available: bool = data.get(
            "available", True
        )  # Whether this emoji can be used

    def __repr__(self) -> str:
        return f"<Emoji id='{self.id}' name='{self.name}' animated={self.animated} available={self.available}>"


class StickerItem:
    """Represents a sticker item, a basic representation of a sticker.

    Used in sticker packs and sometimes in message data.
    """

    def __init__(self, data: Dict[str, Any]):
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.format_type: int = data["format_type"]  # StickerFormatType enum

    def __repr__(self) -> str:
        return f"<StickerItem id='{self.id}' name='{self.name}'>"


class Sticker(StickerItem):
    """Represents a Discord sticker.

    Inherits id, name, format_type from StickerItem.
    """

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        super().__init__(data)
        self._client: Optional["Client"] = client_instance

        self.pack_id: Optional[str] = data.get(
            "pack_id"
        )  # For standard stickers, ID of the pack
        self.description: Optional[str] = data.get("description")
        self.tags: str = data.get(
            "tags", ""
        )  # Comma-separated list of tags for guild stickers
        # type is StickerType enum (STANDARD or GUILD)
        # For guild stickers, this is 2. For standard stickers, this is 1.
        self.type: int = data["type"]
        self.available: bool = data.get(
            "available", True
        )  # Whether this sticker can be used
        self.guild_id: Optional[str] = data.get(
            "guild_id"
        )  # ID of the guild that owns this sticker

        # User object of the user that uploaded the guild sticker
        self.user: Optional[User] = User(data["user"]) if data.get("user") else None

        self.sort_value: Optional[int] = data.get(
            "sort_value"
        )  # The standard sticker's sort order within its pack

    def __repr__(self) -> str:
        return f"<Sticker id='{self.id}' name='{self.name}' guild_id='{self.guild_id}'>"


class StickerPack:
    """Represents a pack of standard stickers."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client: Optional["Client"] = client_instance
        self.id: str = data["id"]
        self.stickers: List[Sticker] = [
            Sticker(s_data, client_instance) for s_data in data.get("stickers", [])
        ]
        self.name: str = data["name"]
        self.sku_id: str = data["sku_id"]
        self.cover_sticker_id: Optional[str] = data.get("cover_sticker_id")
        self.description: str = data["description"]
        self.banner_asset_id: Optional[str] = data.get(
            "banner_asset_id"
        )  # ID of the pack's banner image

    def __repr__(self) -> str:
        return f"<StickerPack id='{self.id}' name='{self.name}' stickers={len(self.stickers)}>"


class PermissionOverwrite:
    """Represents a permission overwrite for a role or member in a channel."""

    def __init__(self, data: Dict[str, Any]):
        self.id: str = data["id"]  # Role or user ID
        self._type_val: int = int(data["type"])  # Store raw type for enum property
        self.allow: str = data["allow"]  # Bitwise value of allowed permissions
        self.deny: str = data["deny"]  # Bitwise value of denied permissions

    @property
    def type(self) -> "OverwriteType":
        from .enums import (
            OverwriteType,
        )  # Local import to avoid circularity at module level

        return OverwriteType(self._type_val)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "allow": self.allow,
            "deny": self.deny,
        }

    def __repr__(self) -> str:
        return f"<PermissionOverwrite id='{self.id}' type='{self.type.name if hasattr(self.type, 'name') else self._type_val}' allow='{self.allow}' deny='{self.deny}'>"


class Guild:
    """Represents a Discord Guild (Server).

    Attributes:
        id (str): Guild ID.
        name (str): Guild name (2-100 characters, excluding @, #, :, ```).
        icon (Optional[str]): Icon hash.
        splash (Optional[str]): Splash hash.
        discovery_splash (Optional[str]): Discovery splash hash; only present for discoverable guilds.
        owner (Optional[bool]): True if the user is the owner of the guild. (Only for /users/@me/guilds endpoint)
        owner_id (str): ID of owner.
        permissions (Optional[str]): Total permissions for the user in the guild (excludes overwrites). (Only for /users/@me/guilds endpoint)
        afk_channel_id (Optional[str]): ID of afk channel.
        afk_timeout (int): AFK timeout in seconds.
        widget_enabled (Optional[bool]): True if the server widget is enabled.
        widget_channel_id (Optional[str]): The channel id that the widget will generate an invite to, or null if set to no invite.
        verification_level (VerificationLevel): Verification level required for the guild.
        default_message_notifications (MessageNotificationLevel): Default message notifications level.
        explicit_content_filter (ExplicitContentFilterLevel): Explicit content filter level.
        roles (List[Role]): Roles in the guild.
        emojis (List[Dict]): Custom emojis. (Consider creating an Emoji model)
        features (List[GuildFeature]): Enabled guild features.
        mfa_level (MFALevel): Required MFA level for the guild.
        application_id (Optional[str]): Application ID of the guild creator if it is bot-created.
        system_channel_id (Optional[str]): The id of the channel where guild notices such as welcome messages and boost events are posted.
        system_channel_flags (int): System channel flags.
        rules_channel_id (Optional[str]): The id of the channel where Community guilds can display rules.
        max_members (Optional[int]): The maximum number of members for the guild.
        vanity_url_code (Optional[str]): The vanity url code for the guild.
        description (Optional[str]): The description of a Community guild.
        banner (Optional[str]): Banner hash.
        premium_tier (PremiumTier): Premium tier (Server Boost level).
        premium_subscription_count (Optional[int]): The number of boosts this guild currently has.
        preferred_locale (str): The preferred locale of a Community guild. Defaults to "en-US".
        public_updates_channel_id (Optional[str]): The id of the channel where admins and moderators of Community guilds receive notices from Discord.
        max_video_channel_users (Optional[int]): The maximum number of users in a video channel.
        welcome_screen (Optional[Dict]): The welcome screen of a Community guild. (Consider a WelcomeScreen model)
        nsfw_level (GuildNSFWLevel): Guild NSFW level.
        stickers (Optional[List[Dict]]): Custom stickers in the guild. (Consider a Sticker model)
        premium_progress_bar_enabled (bool): Whether the guild has the premium progress bar enabled.
    """

    def __init__(self, data: Dict[str, Any], client_instance: "Client"):
        self._client: "Client" = client_instance
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.icon: Optional[str] = data.get("icon")
        self.splash: Optional[str] = data.get("splash")
        self.discovery_splash: Optional[str] = data.get("discovery_splash")
        self.owner: Optional[bool] = data.get("owner")
        self.owner_id: str = data["owner_id"]
        self.permissions: Optional[str] = data.get("permissions")
        self.afk_channel_id: Optional[str] = data.get("afk_channel_id")
        self.afk_timeout: int = data["afk_timeout"]
        self.widget_enabled: Optional[bool] = data.get("widget_enabled")
        self.widget_channel_id: Optional[str] = data.get("widget_channel_id")
        self.verification_level: VerificationLevel = VerificationLevel(
            data["verification_level"]
        )
        self.default_message_notifications: MessageNotificationLevel = (
            MessageNotificationLevel(data["default_message_notifications"])
        )
        self.explicit_content_filter: ExplicitContentFilterLevel = (
            ExplicitContentFilterLevel(data["explicit_content_filter"])
        )

        self.roles: List[Role] = [Role(r) for r in data.get("roles", [])]
        self.emojis: List[Emoji] = [
            Emoji(e_data, client_instance) for e_data in data.get("emojis", [])
        ]

        # Assuming GuildFeature can be constructed from string feature names or their values
        self.features: List[GuildFeature] = [
            GuildFeature(f) if not isinstance(f, GuildFeature) else f
            for f in data.get("features", [])
        ]

        self.mfa_level: MFALevel = MFALevel(data["mfa_level"])
        self.application_id: Optional[str] = data.get("application_id")
        self.system_channel_id: Optional[str] = data.get("system_channel_id")
        self.system_channel_flags: int = data["system_channel_flags"]
        self.rules_channel_id: Optional[str] = data.get("rules_channel_id")
        self.max_members: Optional[int] = data.get("max_members")
        self.vanity_url_code: Optional[str] = data.get("vanity_url_code")
        self.description: Optional[str] = data.get("description")
        self.banner: Optional[str] = data.get("banner")
        self.premium_tier: PremiumTier = PremiumTier(data["premium_tier"])
        self.premium_subscription_count: Optional[int] = data.get(
            "premium_subscription_count"
        )
        self.preferred_locale: str = data.get("preferred_locale", "en-US")
        self.public_updates_channel_id: Optional[str] = data.get(
            "public_updates_channel_id"
        )
        self.max_video_channel_users: Optional[int] = data.get(
            "max_video_channel_users"
        )
        self.approximate_member_count: Optional[int] = data.get(
            "approximate_member_count"
        )
        self.approximate_presence_count: Optional[int] = data.get(
            "approximate_presence_count"
        )
        self.welcome_screen: Optional["WelcomeScreen"] = (
            WelcomeScreen(data["welcome_screen"], client_instance)
            if data.get("welcome_screen")
            else None
        )
        self.nsfw_level: GuildNSFWLevel = GuildNSFWLevel(data["nsfw_level"])
        self.stickers: Optional[List[Sticker]] = (
            [Sticker(s_data, client_instance) for s_data in data.get("stickers", [])]
            if data.get("stickers")
            else None
        )
        self.premium_progress_bar_enabled: bool = data.get(
            "premium_progress_bar_enabled", False
        )

        # Internal caches, populated by events or specific fetches
        self._channels: Dict[str, "Channel"] = {}
        self._members: Dict[str, Member] = {}
        self._threads: Dict[str, "Thread"] = {}

    def get_channel(self, channel_id: str) -> Optional["Channel"]:
        return self._channels.get(channel_id)

    def get_member(self, user_id: str) -> Optional[Member]:
        return self._members.get(user_id)

    def get_member_named(self, name: str) -> Optional[Member]:
        """Retrieve a cached member by username or nickname.

        The lookup is case-insensitive and searches both the username and
        guild nickname for a match.

        Parameters
        ----------
        name: str
            The username or nickname to search for.

        Returns
        -------
        Optional[Member]
            The matching member if found, otherwise ``None``.
        """

        lowered = name.lower()
        for member in self._members.values():
            if member.username.lower() == lowered:
                return member
            if member.nick and member.nick.lower() == lowered:
                return member
        return None

    def get_role(self, role_id: str) -> Optional[Role]:
        return next((role for role in self.roles if role.id == role_id), None)

    def __repr__(self) -> str:
        return f"<Guild id='{self.id}' name='{self.name}'>"


class Channel:
    """Base class for Discord channels."""

    def __init__(self, data: Dict[str, Any], client_instance: "Client"):
        self._client: "Client" = client_instance
        self.id: str = data["id"]
        self._type_val: int = int(data["type"])  # Store raw type for enum property

        self.guild_id: Optional[str] = data.get("guild_id")
        self.name: Optional[str] = data.get("name")
        self.position: Optional[int] = data.get("position")
        self.permission_overwrites: List["PermissionOverwrite"] = [
            PermissionOverwrite(d) for d in data.get("permission_overwrites", [])
        ]
        self.nsfw: Optional[bool] = data.get("nsfw", False)
        self.parent_id: Optional[str] = data.get(
            "parent_id"
        )  # ID of the parent category channel or thread parent

    @property
    def type(self) -> ChannelType:
        return ChannelType(self._type_val)

    @property
    def mention(self) -> str:
        return f"<#{self.id}>"

    async def delete(self, reason: Optional[str] = None):
        await self._client._http.delete_channel(self.id, reason=reason)

    def __repr__(self) -> str:
        return f"<Channel id='{self.id}' name='{self.name}' type='{self.type.name if hasattr(self.type, 'name') else self._type_val}'>"

    def permission_overwrite_for(
        self, target: Union["Role", "Member", str]
    ) -> Optional["PermissionOverwrite"]:
        """Return the :class:`PermissionOverwrite` for ``target`` if present."""

        if isinstance(target, str):
            target_id = target
        else:
            target_id = target.id
        for overwrite in self.permission_overwrites:
            if overwrite.id == target_id:
                return overwrite
        return None

    @staticmethod
    def _apply_overwrite(
        perms: Permissions, overwrite: Optional["PermissionOverwrite"]
    ) -> Permissions:
        if overwrite is None:
            return perms

        perms &= ~Permissions(int(overwrite.deny))
        perms |= Permissions(int(overwrite.allow))
        return perms

    def permissions_for(self, member: "Member") -> Permissions:
        """Resolve channel permissions for ``member``."""

        if self.guild_id is None:
            return Permissions(~0)

        if not hasattr(self._client, "get_guild"):
            return Permissions(0)

        guild = self._client.get_guild(self.guild_id)
        if guild is None:
            return Permissions(0)

        base = Permissions(0)

        everyone = guild.get_role(guild.id)
        if everyone is not None:
            base |= Permissions(int(everyone.permissions))

        for rid in member.roles:
            role = guild.get_role(rid)
            if role is not None:
                base |= Permissions(int(role.permissions))

        if base & Permissions.ADMINISTRATOR:
            return Permissions(~0)

        # Apply @everyone overwrite
        base = self._apply_overwrite(base, self.permission_overwrite_for(guild.id))

        # Role overwrites
        role_allow = Permissions(0)
        role_deny = Permissions(0)
        for rid in member.roles:
            ow = self.permission_overwrite_for(rid)
            if ow is not None:
                role_allow |= Permissions(int(ow.allow))
                role_deny |= Permissions(int(ow.deny))

        base &= ~role_deny
        base |= role_allow

        # Member overwrite
        base = self._apply_overwrite(base, self.permission_overwrite_for(member.id))

        return base


class TextChannel(Channel):
    """Represents a guild text channel or announcement channel."""

    def __init__(self, data: Dict[str, Any], client_instance: "Client"):
        super().__init__(data, client_instance)
        self.topic: Optional[str] = data.get("topic")
        self.last_message_id: Optional[str] = data.get("last_message_id")
        self.rate_limit_per_user: Optional[int] = data.get("rate_limit_per_user", 0)
        self.default_auto_archive_duration: Optional[int] = data.get(
            "default_auto_archive_duration"
        )
        self.last_pin_timestamp: Optional[str] = data.get("last_pin_timestamp")

    def history(
        self,
        *,
        limit: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> AsyncIterator["Message"]:
        """Return an async iterator over this channel's messages."""

        from .utils import message_pager

        return message_pager(self, limit=limit, before=before, after=after)

    async def send(
        self,
        content: Optional[str] = None,
        *,
        embed: Optional[Embed] = None,
        embeds: Optional[List[Embed]] = None,
        components: Optional[List["ActionRow"]] = None,  # Added components
    ) -> "Message":  # Forward reference Message
        if not hasattr(self._client, "send_message"):
            raise NotImplementedError(
                "Client.send_message is required for TextChannel.send"
            )

        return await self._client.send_message(
            channel_id=self.id,
            content=content,
            embed=embed,
            embeds=embeds,
            components=components,
        )

    async def purge(
        self, limit: int, *, before: "Snowflake | None" = None
    ) -> List["Snowflake"]:
        """Bulk delete messages from this channel."""

        params: Dict[str, Union[int, str]] = {"limit": limit}
        if before is not None:
            params["before"] = before

        messages = await self._client._http.request(
            "GET", f"/channels/{self.id}/messages", params=params
        )
        ids = [m["id"] for m in messages]
        if not ids:
            return []

        await self._client._http.bulk_delete_messages(self.id, ids)
        for mid in ids:
            self._client._messages.pop(mid, None)
        return ids

    def __repr__(self) -> str:
        return f"<TextChannel id='{self.id}' name='{self.name}' guild_id='{self.guild_id}'>"


class VoiceChannel(Channel):
    """Represents a guild voice channel or stage voice channel."""

    def __init__(self, data: Dict[str, Any], client_instance: "Client"):
        super().__init__(data, client_instance)
        self.bitrate: int = data.get("bitrate", 64000)
        self.user_limit: int = data.get("user_limit", 0)
        self.rtc_region: Optional[str] = data.get("rtc_region")
        self.video_quality_mode: Optional[int] = data.get("video_quality_mode")

    def __repr__(self) -> str:
        return f"<VoiceChannel id='{self.id}' name='{self.name}' guild_id='{self.guild_id}'>"


class StageChannel(VoiceChannel):
    """Represents a guild stage channel."""

    def __repr__(self) -> str:
        return f"<StageChannel id='{self.id}' name='{self.name}' guild_id='{self.guild_id}'>"

    async def start_stage_instance(
        self,
        topic: str,
        *,
        privacy_level: int = 2,
        reason: Optional[str] = None,
        guild_scheduled_event_id: Optional[str] = None,
    ) -> "StageInstance":
        if not hasattr(self._client, "_http"):
            raise DisagreementException("Client missing HTTP for stage instance")

        payload: Dict[str, Any] = {
            "channel_id": self.id,
            "topic": topic,
            "privacy_level": privacy_level,
        }
        if guild_scheduled_event_id is not None:
            payload["guild_scheduled_event_id"] = guild_scheduled_event_id

        instance = await self._client._http.start_stage_instance(payload, reason=reason)
        instance._client = self._client
        return instance

    async def edit_stage_instance(
        self,
        *,
        topic: Optional[str] = None,
        privacy_level: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> "StageInstance":
        if not hasattr(self._client, "_http"):
            raise DisagreementException("Client missing HTTP for stage instance")

        payload: Dict[str, Any] = {}
        if topic is not None:
            payload["topic"] = topic
        if privacy_level is not None:
            payload["privacy_level"] = privacy_level

        instance = await self._client._http.edit_stage_instance(
            self.id, payload, reason=reason
        )
        instance._client = self._client
        return instance

    async def end_stage_instance(self, *, reason: Optional[str] = None) -> None:
        if not hasattr(self._client, "_http"):
            raise DisagreementException("Client missing HTTP for stage instance")

        await self._client._http.end_stage_instance(self.id, reason=reason)


class StageInstance:
    """Represents a stage instance."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ) -> None:
        self._client = client_instance
        self.id: str = data["id"]
        self.guild_id: Optional[str] = data.get("guild_id")
        self.channel_id: str = data["channel_id"]
        self.topic: str = data["topic"]
        self.privacy_level: int = data.get("privacy_level", 2)
        self.discoverable_disabled: bool = data.get("discoverable_disabled", False)
        self.guild_scheduled_event_id: Optional[str] = data.get(
            "guild_scheduled_event_id"
        )

    def __repr__(self) -> str:
        return f"<StageInstance id='{self.id}' channel_id='{self.channel_id}'>"


class CategoryChannel(Channel):
    """Represents a guild category channel."""

    def __init__(self, data: Dict[str, Any], client_instance: "Client"):
        super().__init__(data, client_instance)

    @property
    def channels(self) -> List[Channel]:
        if not self.guild_id or not hasattr(self._client, "get_guild"):
            return []
        guild = self._client.get_guild(self.guild_id)
        if not guild or not hasattr(
            guild, "_channels"
        ):  # Ensure guild and _channels exist
            return []

        categorized_channels = [
            ch
            for ch in guild._channels.values()
            if getattr(ch, "parent_id", None) == self.id
        ]
        return sorted(
            categorized_channels,
            key=lambda c: c.position if c.position is not None else -1,
        )

    def __repr__(self) -> str:
        return f"<CategoryChannel id='{self.id}' name='{self.name}' guild_id='{self.guild_id}'>"


class ThreadMetadata:
    """Represents the metadata of a thread."""

    def __init__(self, data: Dict[str, Any]):
        self.archived: bool = data["archived"]
        self.auto_archive_duration: int = data["auto_archive_duration"]
        self.archive_timestamp: str = data["archive_timestamp"]
        self.locked: bool = data["locked"]
        self.invitable: Optional[bool] = data.get("invitable")
        self.create_timestamp: Optional[str] = data.get("create_timestamp")


class Thread(TextChannel):  # Threads are a specialized TextChannel
    """Represents a Discord Thread."""

    def __init__(self, data: Dict[str, Any], client_instance: "Client"):
        super().__init__(data, client_instance)  # Handles common text channel fields
        self.owner_id: Optional[str] = data.get("owner_id")
        # parent_id is already handled by base Channel init if present in data
        self.message_count: Optional[int] = data.get("message_count")
        self.member_count: Optional[int] = data.get("member_count")
        self.thread_metadata: ThreadMetadata = ThreadMetadata(data["thread_metadata"])
        self.member: Optional["ThreadMember"] = (
            ThreadMember(data["member"], client_instance)
            if data.get("member")
            else None
        )

    def __repr__(self) -> str:
        return (
            f"<Thread id='{self.id}' name='{self.name}' parent_id='{self.parent_id}'>"
        )


class DMChannel(Channel):
    """Represents a Direct Message channel."""

    def __init__(self, data: Dict[str, Any], client_instance: "Client"):
        super().__init__(data, client_instance)
        self.last_message_id: Optional[str] = data.get("last_message_id")
        self.recipients: List[User] = [
            User(u_data) for u_data in data.get("recipients", [])
        ]

    @property
    def recipient(self) -> Optional[User]:
        return self.recipients[0] if self.recipients else None

    async def send(
        self,
        content: Optional[str] = None,
        *,
        embed: Optional[Embed] = None,
        embeds: Optional[List[Embed]] = None,
        components: Optional[List["ActionRow"]] = None,  # Added components
    ) -> "Message":
        if not hasattr(self._client, "send_message"):
            raise NotImplementedError(
                "Client.send_message is required for DMChannel.send"
            )

        return await self._client.send_message(
            channel_id=self.id,
            content=content,
            embed=embed,
            embeds=embeds,
            components=components,
        )

    async def history(
        self,
        *,
        limit: Optional[int] = 100,
        before: "Snowflake | None" = None,
    ):
        """An async iterator over messages in this DM."""

        params: Dict[str, Union[int, str]] = {}
        if before is not None:
            params["before"] = before

        fetched = 0
        while True:
            to_fetch = 100 if limit is None else min(100, limit - fetched)
            if to_fetch <= 0:
                break
            params["limit"] = to_fetch
            messages = await self._client._http.request(
                "GET", f"/channels/{self.id}/messages", params=params.copy()
            )
            if not messages:
                break
            params["before"] = messages[-1]["id"]
            for msg in messages:
                yield Message(msg, self._client)
                fetched += 1
                if limit is not None and fetched >= limit:
                    return

    def __repr__(self) -> str:
        recipient_repr = self.recipient.username if self.recipient else "Unknown"
        return f"<DMChannel id='{self.id}' recipient='{recipient_repr}'>"


class PartialChannel:
    """Represents a partial channel object, often from interactions."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client: Optional["Client"] = client_instance
        self.id: str = data["id"]
        self.name: Optional[str] = data.get("name")
        self._type_val: int = int(data["type"])
        self.permissions: Optional[str] = data.get("permissions")

    @property
    def type(self) -> ChannelType:
        return ChannelType(self._type_val)

    @property
    def mention(self) -> str:
        return f"<#{self.id}>"

    async def fetch_full_channel(self) -> Optional[Channel]:
        if not self._client or not hasattr(self._client, "fetch_channel"):
            # Log or raise if fetching is not possible
            return None
        try:
            # This assumes Client.fetch_channel exists and returns a full Channel object
            return await self._client.fetch_channel(self.id)
        except HTTPException as exc:
            print(f"HTTP error while fetching channel {self.id}: {exc}")
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            print(f"Failed to parse channel {self.id}: {exc}")
        except DisagreementException as exc:
            print(f"Error fetching channel {self.id}: {exc}")
        return None

    def __repr__(self) -> str:
        type_name = self.type.name if hasattr(self.type, "name") else self._type_val
        return f"<PartialChannel id='{self.id}' name='{self.name}' type='{type_name}'>"


class Webhook:
    """Represents a Discord Webhook."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client: Optional["Client"] = client_instance
        self.id: str = data["id"]
        self.type: int = int(data.get("type", 1))
        self.guild_id: Optional[str] = data.get("guild_id")
        self.channel_id: Optional[str] = data.get("channel_id")
        self.name: Optional[str] = data.get("name")
        self.avatar: Optional[str] = data.get("avatar")
        self.token: Optional[str] = data.get("token")
        self.application_id: Optional[str] = data.get("application_id")
        self.url: Optional[str] = data.get("url")
        self.user: Optional[User] = User(data["user"]) if data.get("user") else None

    def __repr__(self) -> str:
        return f"<Webhook id='{self.id}' name='{self.name}'>"

    @classmethod
    def from_url(
        cls, url: str, session: Optional[aiohttp.ClientSession] = None
    ) -> "Webhook":
        """Create a minimal :class:`Webhook` from a webhook URL.

        Parameters
        ----------
        url:
            The full Discord webhook URL.
        session:
            Unused for now. Present for API compatibility.

        Returns
        -------
        Webhook
            A webhook instance containing only the ``id``, ``token`` and ``url``.
        """

        parts = url.rstrip("/").split("/")
        if len(parts) < 2:
            raise ValueError("Invalid webhook URL")
        token = parts[-1]
        webhook_id = parts[-2]

        return cls({"id": webhook_id, "token": token, "url": url})

    async def send(
        self,
        content: Optional[str] = None,
        *,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        tts: bool = False,
        embed: Optional["Embed"] = None,
        embeds: Optional[List["Embed"]] = None,
        components: Optional[List["ActionRow"]] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Any]] = None,
        files: Optional[List[Any]] = None,
        flags: Optional[int] = None,
    ) -> "Message":
        """Send a message using this webhook."""

        if not self._client:
            raise DisagreementException("Webhook is not bound to a Client")
        assert self.token is not None, "Webhook token missing"

        if embed and embeds:
            raise ValueError("Cannot provide both embed and embeds.")

        final_embeds_payload: Optional[List[Dict[str, Any]]] = None
        if embed:
            final_embeds_payload = [embed.to_dict()]
        elif embeds:
            final_embeds_payload = [e.to_dict() for e in embeds]

        components_payload: Optional[List[Dict[str, Any]]] = None
        if components:
            components_payload = [c.to_dict() for c in components]

        message_data = await self._client._http.execute_webhook(
            self.id,
            self.token,
            content=content,
            tts=tts,
            embeds=final_embeds_payload,
            components=components_payload,
            allowed_mentions=allowed_mentions,
            attachments=attachments,
            files=files,
            flags=flags,
            username=username,
            avatar_url=avatar_url,
        )

        return self._client.parse_message(message_data)


class GuildTemplate:
    """Represents a guild template."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client = client_instance
        self.code: str = data["code"]
        self.name: str = data["name"]
        self.description: Optional[str] = data.get("description")
        self.usage_count: int = data.get("usage_count", 0)
        self.creator_id: str = data.get("creator_id", "")
        self.creator: Optional[User] = (
            User(data["creator"]) if data.get("creator") else None
        )
        self.created_at: Optional[str] = data.get("created_at")
        self.updated_at: Optional[str] = data.get("updated_at")
        self.source_guild_id: Optional[str] = data.get("source_guild_id")
        self.serialized_source_guild: Dict[str, Any] = data.get(
            "serialized_source_guild", {}
        )
        self.is_dirty: Optional[bool] = data.get("is_dirty")

    def __repr__(self) -> str:
        return f"<GuildTemplate code='{self.code}' name='{self.name}'>"


# --- Message Components ---


class Component:
    """Base class for message components."""

    def __init__(self, type: ComponentType):
        self.type: ComponentType = type
        self.custom_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"type": self.type.value}
        if self.custom_id:
            payload["custom_id"] = self.custom_id
        return payload


class ActionRow(Component):
    """Represents an Action Row, a container for other components."""

    def __init__(self, components: Optional[List[Component]] = None):
        super().__init__(ComponentType.ACTION_ROW)
        self.components: List[Component] = components or []

    def add_component(self, component: Component):
        if isinstance(component, ActionRow):
            raise ValueError("Cannot nest ActionRows inside another ActionRow.")

        select_types = {
            ComponentType.STRING_SELECT,
            ComponentType.USER_SELECT,
            ComponentType.ROLE_SELECT,
            ComponentType.MENTIONABLE_SELECT,
            ComponentType.CHANNEL_SELECT,
        }

        if component.type in select_types:
            if self.components:
                raise ValueError(
                    "Select menu components must be the only component in an ActionRow."
                )
            self.components.append(component)
            return self

        if any(c.type in select_types for c in self.components):
            raise ValueError(
                "Cannot add components to an ActionRow that already contains a select menu."
            )

        if len(self.components) >= 5:
            raise ValueError("ActionRow cannot have more than 5 components.")

        self.components.append(component)
        return self

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload["components"] = [c.to_dict() for c in self.components]
        return payload

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], client: Optional["Client"] = None
    ) -> "ActionRow":
        """Deserialize an action row payload."""
        from .components import component_factory

        row = cls()
        for comp_data in data.get("components", []):
            try:
                row.add_component(component_factory(comp_data, client))
            except Exception:
                # Skip components that fail to parse for now
                continue
        return row


class Button(Component):
    """Represents a button component."""

    def __init__(
        self,
        *,  # Make parameters keyword-only for clarity
        style: ButtonStyle,
        label: Optional[str] = None,
        emoji: Optional["PartialEmoji"] = None,  # Changed to PartialEmoji type
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        disabled: bool = False,
    ):
        super().__init__(ComponentType.BUTTON)

        if style == ButtonStyle.LINK and url is None:
            raise ValueError("Link buttons must have a URL.")
        if style != ButtonStyle.LINK and custom_id is None:
            raise ValueError("Non-link buttons must have a custom_id.")
        if label is None and emoji is None:
            raise ValueError("Button must have a label or an emoji.")

        self.style: ButtonStyle = style
        self.label: Optional[str] = label
        self.emoji: Optional[PartialEmoji] = emoji
        self.custom_id = custom_id
        self.url: Optional[str] = url
        self.disabled: bool = disabled

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload["style"] = self.style.value
        if self.label:
            payload["label"] = self.label
        if self.emoji:
            payload["emoji"] = self.emoji.to_dict()  # Call to_dict()
        if self.custom_id:
            payload["custom_id"] = self.custom_id
        if self.url:
            payload["url"] = self.url
        if self.disabled:
            payload["disabled"] = self.disabled
        return payload


class SelectOption:
    """Represents an option in a select menu."""

    def __init__(
        self,
        *,  # Make parameters keyword-only
        label: str,
        value: str,
        description: Optional[str] = None,
        emoji: Optional["PartialEmoji"] = None,  # Changed to PartialEmoji type
        default: bool = False,
    ):
        self.label: str = label
        self.value: str = value
        self.description: Optional[str] = description
        self.emoji: Optional["PartialEmoji"] = emoji
        self.default: bool = default

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "label": self.label,
            "value": self.value,
        }
        if self.description:
            payload["description"] = self.description
        if self.emoji:
            payload["emoji"] = self.emoji.to_dict()  # Call to_dict()
        if self.default:
            payload["default"] = self.default
        return payload


class SelectMenu(Component):
    """Represents a select menu component.

    Currently supports STRING_SELECT (type 3).
    User (5), Role (6), Mentionable (7), Channel (8) selects are not yet fully modeled.
    """

    def __init__(
        self,
        *,  # Make parameters keyword-only
        custom_id: str,
        options: List[SelectOption],
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        channel_types: Optional[List[ChannelType]] = None,
        # For other select types, specific fields would be needed.
        # This constructor primarily targets STRING_SELECT (type 3).
        type: ComponentType = ComponentType.STRING_SELECT,  # Default to string select
    ):
        super().__init__(type)  # Pass the specific select menu type

        if not (1 <= len(options) <= 25):
            raise ValueError("Select menu must have between 1 and 25 options.")
        if not (
            0 <= min_values <= 25
        ):  # Discord docs say min_values can be 0 for some types
            raise ValueError("min_values must be between 0 and 25.")
        if not (1 <= max_values <= 25):
            raise ValueError("max_values must be between 1 and 25.")
        if min_values > max_values:
            raise ValueError("min_values cannot be greater than max_values.")

        self.custom_id = custom_id
        self.options: List[SelectOption] = options
        self.placeholder: Optional[str] = placeholder
        self.min_values: int = min_values
        self.max_values: int = max_values
        self.disabled: bool = disabled
        self.channel_types: Optional[List[ChannelType]] = channel_types

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()  # Gets {"type": self.type.value}
        payload["custom_id"] = self.custom_id
        payload["options"] = [opt.to_dict() for opt in self.options]
        if self.placeholder:
            payload["placeholder"] = self.placeholder
        payload["min_values"] = self.min_values
        payload["max_values"] = self.max_values
        if self.disabled:
            payload["disabled"] = self.disabled
        if self.type == ComponentType.CHANNEL_SELECT and self.channel_types:
            payload["channel_types"] = [ct.value for ct in self.channel_types]
        return payload


class UnfurledMediaItem:
    """Represents an unfurled media item."""

    def __init__(
        self,
        url: str,
        proxy_url: Optional[str] = None,
        height: Optional[int] = None,
        width: Optional[int] = None,
        content_type: Optional[str] = None,
    ):
        self.url = url
        self.proxy_url = proxy_url
        self.height = height
        self.width = width
        self.content_type = content_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "proxy_url": self.proxy_url,
            "height": self.height,
            "width": self.width,
            "content_type": self.content_type,
        }


class MediaGalleryItem:
    """Represents an item in a media gallery."""

    def __init__(
        self,
        media: UnfurledMediaItem,
        description: Optional[str] = None,
        spoiler: bool = False,
    ):
        self.media = media
        self.description = description
        self.spoiler = spoiler

    def to_dict(self) -> Dict[str, Any]:
        return {
            "media": self.media.to_dict(),
            "description": self.description,
            "spoiler": self.spoiler,
        }


class TextDisplay(Component):
    """Represents a text display component."""

    def __init__(self, content: str, id: Optional[int] = None):
        super().__init__(ComponentType.TEXT_DISPLAY)
        self.content = content
        self.id = id

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload["content"] = self.content
        if self.id is not None:
            payload["id"] = self.id
        return payload


class Thumbnail(Component):
    """Represents a thumbnail component."""

    def __init__(
        self,
        media: UnfurledMediaItem,
        description: Optional[str] = None,
        spoiler: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(ComponentType.THUMBNAIL)
        self.media = media
        self.description = description
        self.spoiler = spoiler
        self.id = id

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload["media"] = self.media.to_dict()
        if self.description:
            payload["description"] = self.description
        if self.spoiler:
            payload["spoiler"] = self.spoiler
        if self.id is not None:
            payload["id"] = self.id
        return payload


class Section(Component):
    """Represents a section component."""

    def __init__(
        self,
        components: List[TextDisplay],
        accessory: Optional[Union[Thumbnail, Button]] = None,
        id: Optional[int] = None,
    ):
        super().__init__(ComponentType.SECTION)
        self.components = components
        self.accessory = accessory
        self.id = id

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload["components"] = [c.to_dict() for c in self.components]
        if self.accessory:
            payload["accessory"] = self.accessory.to_dict()
        if self.id is not None:
            payload["id"] = self.id
        return payload


class MediaGallery(Component):
    """Represents a media gallery component."""

    def __init__(self, items: List[MediaGalleryItem], id: Optional[int] = None):
        super().__init__(ComponentType.MEDIA_GALLERY)
        self.items = items
        self.id = id

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload["items"] = [i.to_dict() for i in self.items]
        if self.id is not None:
            payload["id"] = self.id
        return payload


class FileComponent(Component):
    """Represents a file component."""

    def __init__(
        self, file: UnfurledMediaItem, spoiler: bool = False, id: Optional[int] = None
    ):
        super().__init__(ComponentType.FILE)
        self.file = file
        self.spoiler = spoiler
        self.id = id

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload["file"] = self.file.to_dict()
        if self.spoiler:
            payload["spoiler"] = self.spoiler
        if self.id is not None:
            payload["id"] = self.id
        return payload


class Separator(Component):
    """Represents a separator component."""

    def __init__(
        self, divider: bool = True, spacing: int = 1, id: Optional[int] = None
    ):
        super().__init__(ComponentType.SEPARATOR)
        self.divider = divider
        self.spacing = spacing
        self.id = id

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload["divider"] = self.divider
        payload["spacing"] = self.spacing
        if self.id is not None:
            payload["id"] = self.id
        return payload


class Container(Component):
    """Represents a container component."""

    def __init__(
        self,
        components: List[Component],
        accent_color: Color | int | str | None = None,
        spoiler: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(ComponentType.CONTAINER)
        self.components = components
        self.accent_color = Color.parse(accent_color)
        self.spoiler = spoiler
        self.id = id

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload["components"] = [c.to_dict() for c in self.components]
        if self.accent_color:
            payload["accent_color"] = self.accent_color.value
        if self.spoiler:
            payload["spoiler"] = self.spoiler
        if self.id is not None:
            payload["id"] = self.id
        return payload


class WelcomeChannel:
    """Represents a channel shown in the server's welcome screen.

    Attributes:
        channel_id (str): The ID of the channel.
        description (str): The description shown for the channel.
        emoji_id (Optional[str]): The ID of the emoji, if custom.
        emoji_name (Optional[str]): The name of the emoji if custom, or the unicode character if standard.
    """

    def __init__(self, data: Dict[str, Any]):
        self.channel_id: str = data["channel_id"]
        self.description: str = data["description"]
        self.emoji_id: Optional[str] = data.get("emoji_id")
        self.emoji_name: Optional[str] = data.get("emoji_name")

    def __repr__(self) -> str:
        return (
            f"<WelcomeChannel id='{self.channel_id}' description='{self.description}'>"
        )


class WelcomeScreen:
    """Represents the welcome screen of a Community guild.

    Attributes:
        description (Optional[str]): The server description shown in the welcome screen.
        welcome_channels (List[WelcomeChannel]): The channels shown in the welcome screen.
    """

    def __init__(self, data: Dict[str, Any], client_instance: "Client"):
        self._client: "Client" = (
            client_instance  # May be useful for fetching channel objects
        )
        self.description: Optional[str] = data.get("description")
        self.welcome_channels: List[WelcomeChannel] = [
            WelcomeChannel(wc_data) for wc_data in data.get("welcome_channels", [])
        ]

    def __repr__(self) -> str:
        return f"<WelcomeScreen description='{self.description}' channels={len(self.welcome_channels)}>"


class ThreadMember:
    """Represents a member of a thread.

    Attributes:
        id (Optional[str]): The ID of the thread. Not always present.
        user_id (Optional[str]): The ID of the user. Not always present.
        join_timestamp (str): When the user joined the thread (ISO8601 timestamp).
        flags (int): User-specific flags for thread settings.
        member (Optional[Member]): The guild member object for this user, if resolved.
                                   Only available from GUILD_MEMBERS intent and if fetched.
    """

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):  # client_instance for member resolution
        self._client: Optional["Client"] = client_instance
        self.id: Optional[str] = data.get("id")  # Thread ID
        self.user_id: Optional[str] = data.get("user_id")
        self.join_timestamp: str = data["join_timestamp"]
        self.flags: int = data["flags"]

        # The 'member' field in ThreadMember payload is a full guild member object.
        # This is present in some contexts like when listing thread members.
        self.member: Optional[Member] = (
            Member(data["member"], client_instance) if data.get("member") else None
        )

        # Note: The 'presence' field is not included as it's often unavailable or too dynamic for a simple model.

    def __repr__(self) -> str:
        return f"<ThreadMember user_id='{self.user_id}' thread_id='{self.id}'>"


class PresenceUpdate:
    """Represents a PRESENCE_UPDATE event."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client = client_instance
        self.user = User(data["user"])
        self.guild_id: Optional[str] = data.get("guild_id")
        self.status: Optional[str] = data.get("status")
        self.activities: List[Dict[str, Any]] = data.get("activities", [])
        self.client_status: Dict[str, Any] = data.get("client_status", {})

    def __repr__(self) -> str:
        return f"<PresenceUpdate user_id='{self.user.id}' guild_id='{self.guild_id}' status='{self.status}'>"


class TypingStart:
    """Represents a TYPING_START event."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client = client_instance
        self.channel_id: str = data["channel_id"]
        self.guild_id: Optional[str] = data.get("guild_id")
        self.user_id: str = data["user_id"]
        self.timestamp: int = data["timestamp"]
        self.member: Optional[Member] = (
            Member(data["member"], client_instance) if data.get("member") else None
        )

    def __repr__(self) -> str:
        return f"<TypingStart channel_id='{self.channel_id}' user_id='{self.user_id}'>"


class Reaction:
    """Represents a message reaction event."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client = client_instance
        self.user_id: str = data["user_id"]
        self.channel_id: str = data["channel_id"]
        self.message_id: str = data["message_id"]
        self.guild_id: Optional[str] = data.get("guild_id")
        self.member: Optional[Member] = (
            Member(data["member"], client_instance) if data.get("member") else None
        )
        self.emoji: Dict[str, Any] = data.get("emoji", {})

    def __repr__(self) -> str:
        emoji_value = self.emoji.get("name") or self.emoji.get("id")
        return f"<Reaction message_id='{self.message_id}' user_id='{self.user_id}' emoji='{emoji_value}'>"


class ScheduledEvent:
    """Represents a guild scheduled event."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client = client_instance
        self.id: str = data["id"]
        self.guild_id: str = data["guild_id"]
        self.channel_id: Optional[str] = data.get("channel_id")
        self.creator_id: Optional[str] = data.get("creator_id")
        self.name: str = data["name"]
        self.description: Optional[str] = data.get("description")
        self.scheduled_start_time: str = data["scheduled_start_time"]
        self.scheduled_end_time: Optional[str] = data.get("scheduled_end_time")
        self.privacy_level: GuildScheduledEventPrivacyLevel = (
            GuildScheduledEventPrivacyLevel(data["privacy_level"])
        )
        self.status: GuildScheduledEventStatus = GuildScheduledEventStatus(
            data["status"]
        )
        self.entity_type: GuildScheduledEventEntityType = GuildScheduledEventEntityType(
            data["entity_type"]
        )
        self.entity_id: Optional[str] = data.get("entity_id")
        self.entity_metadata: Optional[Dict[str, Any]] = data.get("entity_metadata")
        self.creator: Optional[User] = (
            User(data["creator"]) if data.get("creator") else None
        )
        self.user_count: Optional[int] = data.get("user_count")
        self.image: Optional[str] = data.get("image")

    def __repr__(self) -> str:
        return f"<ScheduledEvent id='{self.id}' name='{self.name}'>"


@dataclass
class Invite:
    """Represents a Discord invite."""

    code: str
    channel_id: Optional[str]
    guild_id: Optional[str]
    inviter_id: Optional[str]
    uses: Optional[int]
    max_uses: Optional[int]
    max_age: Optional[int]
    temporary: Optional[bool]
    created_at: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Invite":
        channel = data.get("channel")
        guild = data.get("guild")
        inviter = data.get("inviter")
        return cls(
            code=data["code"],
            channel_id=(channel or {}).get("id") if channel else data.get("channel_id"),
            guild_id=(guild or {}).get("id") if guild else data.get("guild_id"),
            inviter_id=(inviter or {}).get("id"),
            uses=data.get("uses"),
            max_uses=data.get("max_uses"),
            max_age=data.get("max_age"),
            temporary=data.get("temporary"),
            created_at=data.get("created_at"),
        )

    def __repr__(self) -> str:
        return f"<Invite code='{self.code}' guild_id='{self.guild_id}' channel_id='{self.channel_id}'>"


class GuildMemberRemove:
    """Represents a GUILD_MEMBER_REMOVE event."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client = client_instance
        self.guild_id: str = data["guild_id"]
        self.user: User = User(data["user"])

    def __repr__(self) -> str:
        return (
            f"<GuildMemberRemove guild_id='{self.guild_id}' user_id='{self.user.id}'>"
        )


class GuildBanAdd:
    """Represents a GUILD_BAN_ADD event."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client = client_instance
        self.guild_id: str = data["guild_id"]
        self.user: User = User(data["user"])

    def __repr__(self) -> str:
        return f"<GuildBanAdd guild_id='{self.guild_id}' user_id='{self.user.id}'>"


class GuildBanRemove:
    """Represents a GUILD_BAN_REMOVE event."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client = client_instance
        self.guild_id: str = data["guild_id"]
        self.user: User = User(data["user"])

    def __repr__(self) -> str:
        return f"<GuildBanRemove guild_id='{self.guild_id}' user_id='{self.user.id}'>"


class GuildRoleUpdate:
    """Represents a GUILD_ROLE_UPDATE event."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ):
        self._client = client_instance
        self.guild_id: str = data["guild_id"]
        self.role: Role = Role(data["role"])

    def __repr__(self) -> str:
        return f"<GuildRoleUpdate guild_id='{self.guild_id}' role_id='{self.role.id}'>"


class AuditLogEntry:
    """Represents a single entry in a guild's audit log."""

    def __init__(
        self, data: Dict[str, Any], client_instance: Optional["Client"] = None
    ) -> None:
        self._client = client_instance
        self.id: str = data["id"]
        self.user_id: Optional[str] = data.get("user_id")
        self.target_id: Optional[str] = data.get("target_id")
        self.action_type: int = data["action_type"]
        self.reason: Optional[str] = data.get("reason")
        self.changes: List[Dict[str, Any]] = data.get("changes", [])
        self.options: Optional[Dict[str, Any]] = data.get("options")

    def __repr__(self) -> str:
        return f"<AuditLogEntry id='{self.id}' action_type={self.action_type} user_id='{self.user_id}'>"


def channel_factory(data: Dict[str, Any], client: "Client") -> Channel:
    """Create a channel object from raw API data."""
    channel_type = data.get("type")

    if channel_type in (
        ChannelType.GUILD_TEXT.value,
        ChannelType.GUILD_ANNOUNCEMENT.value,
    ):
        return TextChannel(data, client)
    if channel_type == ChannelType.GUILD_VOICE.value:
        return VoiceChannel(data, client)
    if channel_type == ChannelType.GUILD_STAGE_VOICE.value:
        return StageChannel(data, client)
    if channel_type == ChannelType.GUILD_CATEGORY.value:
        return CategoryChannel(data, client)
    if channel_type in (
        ChannelType.ANNOUNCEMENT_THREAD.value,
        ChannelType.PUBLIC_THREAD.value,
        ChannelType.PRIVATE_THREAD.value,
    ):
        return Thread(data, client)
    if channel_type in (ChannelType.DM.value, ChannelType.GROUP_DM.value):
        return DMChannel(data, client)

    return Channel(data, client)
