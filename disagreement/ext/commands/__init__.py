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
    max_concurrency,
    requires_permissions,
    has_role,
    has_any_role,
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
    MaxConcurrencyReached,
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
    "max_concurrency",
    "requires_permissions",
    "has_role",
    "has_any_role",
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
    "MaxConcurrencyReached",
]
