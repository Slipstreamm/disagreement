"""
Disagreement
~~~~~~~~~~~~

A Python library for interacting with the Discord API.

:copyright: (c) 2025 Slipstream
:license: BSD 3-Clause License, see LICENSE for more details.
"""

__title__ = "disagreement"
__author__ = "Slipstream"
__license__ = "BSD 3-Clause License"
__copyright__ = "Copyright 2025 Slipstream"
__version__ = "0.7.0"

from .client import Client, AutoShardedClient
from .models import (
    Message,
    User,
    Reaction,
    AuditLogEntry,
    Member,
    Role,
    Attachment,
    Channel,
    ActionRow,
    Button,
    SelectOption,
    SelectMenu,
    Embed,
    PartialEmoji,
    Section,
    TextDisplay,
    Thumbnail,
    UnfurledMediaItem,
    MediaGallery,
    MediaGalleryItem,
    Container,
    Guild,
)
from .voice_client import VoiceClient
from .audio import AudioSource, FFmpegAudioSource
from .typing import Typing
from .errors import (
    DisagreementException,
    HTTPException,
    GatewayException,
    AuthenticationError,
    Forbidden,
    NotFound,
)
from .color import Color
from .utils import utcnow, message_pager
from .enums import (
    GatewayIntent,
    GatewayOpcode,
    ButtonStyle,
    ChannelType,
    MessageFlags,
    InteractionType,
    InteractionCallbackType,
    ComponentType,
)
from .error_handler import setup_global_error_handler
from .hybrid_context import HybridContext
from .interactions import Interaction
from .logging_config import setup_logging
from . import ui, ext
from .ext.app_commands import (
    AppCommand,
    AppCommandContext,
    AppCommandGroup,
    MessageCommand,
    OptionMetadata,
    SlashCommand,
    UserCommand,
    group,
    hybrid_command,
    message_command,
    slash_command,
    subcommand,
    subcommand_group,
)
from .ext.commands import (
    BadArgument,
    CheckAnyFailure,
    CheckFailure,
    Cog,
    Command,
    CommandContext,
    CommandError,
    CommandInvokeError,
    CommandNotFound,
    CommandOnCooldown,
    MaxConcurrencyReached,
    MissingRequiredArgument,
    ArgumentParsingError,
    check,
    check_any,
    command,
    cooldown,
    has_any_role,
    has_role,
    listener,
    max_concurrency,
    requires_permissions,
)
from .ext.tasks import Task, loop
from .ui import Item, Modal, Select, TextInput, View, button, select, text_input


import logging


__all__ = [
    "Client",
    "AutoShardedClient",
    "Message",
    "User",
    "Reaction",
    "AuditLogEntry",
    "Member",
    "Role",
    "Attachment",
    "Channel",
    "ActionRow",
    "Button",
    "SelectOption",
    "SelectMenu",
    "Embed",
    "PartialEmoji",
    "Section",
    "TextDisplay",
    "Thumbnail",
    "UnfurledMediaItem",
    "MediaGallery",
    "MediaGalleryItem",
    "Container",
    "VoiceClient",
    "AudioSource",
    "FFmpegAudioSource",
    "Typing",
    "DisagreementException",
    "HTTPException",
    "GatewayException",
    "AuthenticationError",
    "Forbidden",
    "NotFound",
    "Color",
    "utcnow",
    "message_pager",
    "GatewayIntent",
    "GatewayOpcode",
    "ButtonStyle",
    "ChannelType",
    "MessageFlags",
    "InteractionType",
    "InteractionCallbackType",
    "ComponentType",
    "setup_global_error_handler",
    "HybridContext",
    "Interaction",
    "setup_logging",
    "ui",
    "ext",
    "AppCommand",
    "AppCommandContext",
    "AppCommandGroup",
    "MessageCommand",
    "OptionMetadata",
    "SlashCommand",
    "UserCommand",
    "group",
    "hybrid_command",
    "message_command",
    "slash_command",
    "subcommand",
    "subcommand_group",
    "BadArgument",
    "CheckAnyFailure",
    "CheckFailure",
    "Cog",
    "Command",
    "CommandContext",
    "CommandError",
    "CommandInvokeError",
    "CommandNotFound",
    "CommandOnCooldown",
    "MaxConcurrencyReached",
    "MissingRequiredArgument",
    "ArgumentParsingError",
    "check",
    "check_any",
    "command",
    "cooldown",
    "has_any_role",
    "has_role",
    "listener",
    "max_concurrency",
    "requires_permissions",
    "Task",
    "loop",
    "Item",
    "Modal",
    "Select",
    "TextInput",
    "View",
    "button",
    "select",
    "text_input",
]


# Configure a default logger if none has been configured yet
if not logging.getLogger().hasHandlers():
    setup_logging(logging.INFO)
