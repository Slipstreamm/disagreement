# disagreement/ext/commands/__init__.py

"""
disagreement.ext.commands - A command framework extension for the Disagreement library.
"""

from .cog import Cog
from .core import (
    Command,
    CommandContext,
    CommandHandler,
)  # CommandHandler might be internal
from .decorators import (
    command,
    listener,
    check,
    check_any,
    cooldown,
    requires_permissions,
)
from .errors import (
    CommandError,
    CommandNotFound,
    BadArgument,
    MissingRequiredArgument,
    ArgumentParsingError,
    CheckFailure,
    CheckAnyFailure,
    CommandOnCooldown,
    CommandInvokeError,
)

__all__ = [
    # Cog
    "Cog",
    # Core
    "Command",
    "CommandContext",
    # "CommandHandler", # Usually not part of public API for direct use by bot devs
    # Decorators
    "command",
    "listener",
    "check",
    "check_any",
    "cooldown",
    "requires_permissions",
    # Errors
    "CommandError",
    "CommandNotFound",
    "BadArgument",
    "MissingRequiredArgument",
    "ArgumentParsingError",
    "CheckFailure",
    "CheckAnyFailure",
    "CommandOnCooldown",
    "CommandInvokeError",
]
