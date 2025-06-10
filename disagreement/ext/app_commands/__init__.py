# disagreement/ext/app_commands/__init__.py

"""
Application Commands Extension for Disagreement.

This package provides the framework for creating and handling
Discord Application Commands (slash commands, user commands, message commands).
"""

from .commands import (
    AppCommand,
    SlashCommand,
    UserCommand,
    MessageCommand,
    AppCommandGroup,
)
from .decorators import (
    slash_command,
    user_command,
    message_command,
    hybrid_command,
    group,
    subcommand,
    subcommand_group,
    OptionMetadata,
)
from .context import AppCommandContext

# from .handler import AppCommandHandler # Will be imported when defined

__all__ = [
    "AppCommand",
    "SlashCommand",
    "UserCommand",
    "MessageCommand",
    "AppCommandGroup",  # To be defined
    "slash_command",
    "user_command",
    "message_command",
    "hybrid_command",
    "group",
    "subcommand",
    "subcommand_group",
    "OptionMetadata",
    "AppCommandContext",  # To be defined
]
