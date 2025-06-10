# disagreement/ext/commands/errors.py

"""
Custom exceptions for the command extension.
"""

from disagreement.errors import DisagreementException


class CommandError(DisagreementException):
    """Base exception for errors raised by the commands extension."""

    pass


class CommandNotFound(CommandError):
    """Exception raised when a command is not found."""

    def __init__(self, command_name: str):
        self.command_name = command_name
        super().__init__(f"Command '{command_name}' not found.")


class BadArgument(CommandError):
    """Exception raised when a command argument fails to parse or validate."""

    pass


class MissingRequiredArgument(BadArgument):
    """Exception raised when a required command argument is missing."""

    def __init__(self, param_name: str):
        self.param_name = param_name
        super().__init__(f"Missing required argument: {param_name}")


class ArgumentParsingError(BadArgument):
    """Exception raised during the argument parsing process."""

    pass


class CheckFailure(CommandError):
    """Exception raised when a command check fails."""

    pass


class CheckAnyFailure(CheckFailure):
    """Raised when :func:`check_any` fails all checks."""

    def __init__(self, errors: list[CheckFailure]):
        self.errors = errors
        msg = "; ".join(str(e) for e in errors)
        super().__init__(f"All checks failed: {msg}")


class CommandOnCooldown(CheckFailure):
    """Raised when a command is invoked while on cooldown."""

    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Command is on cooldown. Retry in {retry_after:.2f}s")


class CommandInvokeError(CommandError):
    """Exception raised when an error occurs during command invocation."""

    def __init__(self, original: Exception):
        self.original = original
        super().__init__(f"Error during command invocation: {original}")


# Add more specific errors as needed, e.g., UserNotFound, ChannelNotFound, etc.
# These might inherit from BadArgument.
