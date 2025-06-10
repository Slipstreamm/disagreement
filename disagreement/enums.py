# disagreement/enums.py

"""
Enums for Discord constants.
"""

from enum import IntEnum, Enum  # Import Enum


class GatewayOpcode(IntEnum):
    """Represents a Discord Gateway Opcode."""

    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11


class GatewayIntent(IntEnum):
    """Represents a Discord Gateway Intent bit.

    Intents are used to subscribe to specific groups of events from the Gateway.
    """

    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1  # Privileged
    GUILD_MODERATION = 1 << 2  # Formerly GUILD_BANS
    GUILD_EMOJIS_AND_STICKERS = 1 << 3
    GUILD_INTEGRATIONS = 1 << 4
    GUILD_WEBHOOKS = 1 << 5
    GUILD_INVITES = 1 << 6
    GUILD_VOICE_STATES = 1 << 7
    GUILD_PRESENCES = 1 << 8  # Privileged
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    GUILD_MESSAGE_TYPING = 1 << 11
    DIRECT_MESSAGES = 1 << 12
    DIRECT_MESSAGE_REACTIONS = 1 << 13
    DIRECT_MESSAGE_TYPING = 1 << 14
    MESSAGE_CONTENT = 1 << 15  # Privileged (as of Aug 31, 2022)
    GUILD_SCHEDULED_EVENTS = 1 << 16
    AUTO_MODERATION_CONFIGURATION = 1 << 20
    AUTO_MODERATION_EXECUTION = 1 << 21

    @classmethod
    def none(cls) -> int:
        """Return a bitmask representing no intents."""
        return 0

    @classmethod
    def default(cls) -> int:
        """Returns default intents (excluding privileged ones like members, presences, message content)."""
        return (
            cls.GUILDS
            | cls.GUILD_MODERATION
            | cls.GUILD_EMOJIS_AND_STICKERS
            | cls.GUILD_INTEGRATIONS
            | cls.GUILD_WEBHOOKS
            | cls.GUILD_INVITES
            | cls.GUILD_VOICE_STATES
            | cls.GUILD_MESSAGES
            | cls.GUILD_MESSAGE_REACTIONS
            | cls.GUILD_MESSAGE_TYPING
            | cls.DIRECT_MESSAGES
            | cls.DIRECT_MESSAGE_REACTIONS
            | cls.DIRECT_MESSAGE_TYPING
            | cls.GUILD_SCHEDULED_EVENTS
            | cls.AUTO_MODERATION_CONFIGURATION
            | cls.AUTO_MODERATION_EXECUTION
        )

    @classmethod
    def all(cls) -> int:
        """Returns all intents, including privileged ones. Use with caution."""
        val = 0
        for intent in cls:
            val |= intent.value
        return val

    @classmethod
    def privileged(cls) -> int:
        """Returns a bitmask of all privileged intents."""
        return cls.GUILD_MEMBERS | cls.GUILD_PRESENCES | cls.MESSAGE_CONTENT


# --- Application Command Enums ---


class ApplicationCommandType(IntEnum):
    """Type of application command."""

    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3
    PRIMARY_ENTRY_POINT = 4


class ApplicationCommandOptionType(IntEnum):
    """Type of application command option."""

    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4  # Any integer between -2^53 and 2^53
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7  # Includes all channel types + categories
    ROLE = 8
    MENTIONABLE = 9  # Includes users and roles
    NUMBER = 10  # Any double between -2^53 and 2^53
    ATTACHMENT = 11


class InteractionType(IntEnum):
    """Type of interaction."""

    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class InteractionCallbackType(IntEnum):
    """Type of interaction callback."""

    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9  # Response to send a modal


class IntegrationType(IntEnum):
    """
    Installation context(s) where the command is available,
    only for globally-scoped commands.
    """

    GUILD_INSTALL = (
        0  # Command is available when the app is installed to a guild (default)
    )
    USER_INSTALL = 1  # Command is available when the app is installed to a user


class InteractionContextType(IntEnum):
    """
    Interaction context(s) where the command can be used,
    only for globally-scoped commands.
    """

    GUILD = 0  # Command can be used in guilds
    BOT_DM = 1  # Command can be used in DMs with the app's bot user
    PRIVATE_CHANNEL = 2  # Command can be used in Group DMs and DMs (requires USER_INSTALL integration_type)


class MessageFlags(IntEnum):
    """Represents the flags of a message."""

    CROSSPOSTED = 1 << 0
    IS_CROSSPOST = 1 << 1
    SUPPRESS_EMBEDS = 1 << 2
    SOURCE_MESSAGE_DELETED = 1 << 3
    URGENT = 1 << 4
    HAS_THREAD = 1 << 5
    EPHEMERAL = 1 << 6
    LOADING = 1 << 7
    FAILED_TO_MENTION_SOME_ROLES_IN_THREAD = 1 << 8
    SUPPRESS_NOTIFICATIONS = (
        1 << 12
    )  # Discord specific, was previously 1 << 4 (IS_VOICE_MESSAGE)
    IS_COMPONENTS_V2 = 1 << 15


# --- Guild Enums ---


class VerificationLevel(IntEnum):
    """Guild verification level."""

    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4


class MessageNotificationLevel(IntEnum):
    """Default message notification level for a guild."""

    ALL_MESSAGES = 0
    ONLY_MENTIONS = 1


class ExplicitContentFilterLevel(IntEnum):
    """Explicit content filter level for a guild."""

    DISABLED = 0
    MEMBERS_WITHOUT_ROLES = 1
    ALL_MEMBERS = 2


class MFALevel(IntEnum):
    """Multi-Factor Authentication level for a guild."""

    NONE = 0
    ELEVATED = 1


class GuildNSFWLevel(IntEnum):
    """NSFW level of a guild."""

    DEFAULT = 0
    EXPLICIT = 1
    SAFE = 2
    AGE_RESTRICTED = 3


class PremiumTier(IntEnum):
    """Guild premium tier (boost level)."""

    NONE = 0
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class GuildFeature(str, Enum):  # Changed from IntEnum to Enum
    """Features that a guild can have.

    Note: This is not an exhaustive list and Discord may add more.
    Using str as a base allows for unknown features to be stored as strings.
    """

    ANIMATED_BANNER = "ANIMATED_BANNER"
    ANIMATED_ICON = "ANIMATED_ICON"
    APPLICATION_COMMAND_PERMISSIONS_V2 = "APPLICATION_COMMAND_PERMISSIONS_V2"
    AUTO_MODERATION = "AUTO_MODERATION"
    BANNER = "BANNER"
    COMMUNITY = "COMMUNITY"
    CREATOR_MONETIZABLE_PROVISIONAL = "CREATOR_MONETIZABLE_PROVISIONAL"
    CREATOR_STORE_PAGE = "CREATOR_STORE_PAGE"
    DEVELOPER_SUPPORT_SERVER = "DEVELOPER_SUPPORT_SERVER"
    DISCOVERABLE = "DISCOVERABLE"
    FEATURABLE = "FEATURABLE"
    INVITES_DISABLED = "INVITES_DISABLED"
    INVITE_SPLASH = "INVITE_SPLASH"
    MEMBER_VERIFICATION_GATE_ENABLED = "MEMBER_VERIFICATION_GATE_ENABLED"
    MORE_STICKERS = "MORE_STICKERS"
    NEWS = "NEWS"
    PARTNERED = "PARTNERED"
    PREVIEW_ENABLED = "PREVIEW_ENABLED"
    RAID_ALERTS_DISABLED = "RAID_ALERTS_DISABLED"
    ROLE_ICONS = "ROLE_ICONS"
    ROLE_SUBSCRIPTIONS_AVAILABLE_FOR_PURCHASE = (
        "ROLE_SUBSCRIPTIONS_AVAILABLE_FOR_PURCHASE"
    )
    ROLE_SUBSCRIPTIONS_ENABLED = "ROLE_SUBSCRIPTIONS_ENABLED"
    TICKETED_EVENTS_ENABLED = "TICKETED_EVENTS_ENABLED"
    VANITY_URL = "VANITY_URL"
    VERIFIED = "VERIFIED"
    VIP_REGIONS = "VIP_REGIONS"
    WELCOME_SCREEN_ENABLED = "WELCOME_SCREEN_ENABLED"
    # Add more as they become known or needed

    # This allows GuildFeature("UNKNOWN_FEATURE_STRING") to work
    @classmethod
    def _missing_(cls, value):  # type: ignore
        return str(value)


# --- Channel Enums ---


class ChannelType(IntEnum):
    """Type of channel."""

    GUILD_TEXT = 0  # a text channel within a server
    DM = 1  # a direct message between users
    GUILD_VOICE = 2  # a voice channel within a server
    GROUP_DM = 3  # a direct message between multiple users
    GUILD_CATEGORY = 4  # an organizational category that contains up to 50 channels
    GUILD_ANNOUNCEMENT = 5  # a channel that users can follow and crosspost into their own server (formerly GUILD_NEWS)
    ANNOUNCEMENT_THREAD = (
        10  # a temporary sub-channel within a GUILD_ANNOUNCEMENT channel
    )
    PUBLIC_THREAD = (
        11  # a temporary sub-channel within a GUILD_TEXT or GUILD_ANNOUNCEMENT channel
    )
    PRIVATE_THREAD = 12  # a temporary sub-channel within a GUILD_TEXT channel that is only viewable by those invited and those with the MANAGE_THREADS permission
    GUILD_STAGE_VOICE = (
        13  # a voice channel for hosting events with speakers and audiences
    )
    GUILD_DIRECTORY = 14  # a channel in a hub containing the listed servers
    GUILD_FORUM = 15  # (Still in development) a channel that can only contain threads
    GUILD_MEDIA = 16  # (Still in development) a channel that can only contain media


class OverwriteType(IntEnum):
    """Type of target for a permission overwrite."""

    ROLE = 0
    MEMBER = 1


# --- Component Enums ---


class ComponentType(IntEnum):
    """Type of message component."""

    ACTION_ROW = 1
    BUTTON = 2
    STRING_SELECT = 3  # Formerly SELECT_MENU
    TEXT_INPUT = 4
    USER_SELECT = 5
    ROLE_SELECT = 6
    MENTIONABLE_SELECT = 7
    CHANNEL_SELECT = 8
    SECTION = 9
    TEXT_DISPLAY = 10
    THUMBNAIL = 11
    MEDIA_GALLERY = 12
    FILE = 13
    SEPARATOR = 14
    CONTAINER = 17


class ButtonStyle(IntEnum):
    """Style of a button component."""

    # Blurple
    PRIMARY = 1
    # Grey
    SECONDARY = 2
    # Green
    SUCCESS = 3
    # Red
    DANGER = 4
    # Grey, navigates to a URL
    LINK = 5


class TextInputStyle(IntEnum):
    """Style of a text input component."""

    SHORT = 1
    PARAGRAPH = 2


# Example of how you might combine intents:
# intents = GatewayIntent.GUILDS | GatewayIntent.GUILD_MESSAGES | GatewayIntent.MESSAGE_CONTENT
# client = Client(token="YOUR_TOKEN", intents=intents)
