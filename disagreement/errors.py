# disagreement/errors.py

"""
Custom exceptions for the Disagreement library.
"""

from typing import Optional, Any  # Add Optional and Any here


class DisagreementException(Exception):
    """Base exception class for all errors raised by this library."""

    pass


class HTTPException(DisagreementException):
    """Exception raised for HTTP-related errors.

    Attributes:
        response: The aiohttp response object, if available.
        status: The HTTP status code.
        text: The response text, if available.
        error_code: Discord specific error code, if available.
    """

    def __init__(
        self, response=None, message=None, *, status=None, text=None, error_code=None
    ):
        self.response = response
        self.status = status or (response.status if response else None)
        self.text = text or (
            response.text if response else None
        )  # Or await response.text() if in async context
        self.error_code = error_code

        full_message = f"HTTP {self.status}"
        if message:
            full_message += f": {message}"
        elif self.text:
            full_message += f": {self.text}"
        if self.error_code:
            full_message += f" (Discord Error Code: {self.error_code})"

        super().__init__(full_message)


class GatewayException(DisagreementException):
    """Exception raised for errors related to the Discord Gateway connection or protocol."""

    pass


class AuthenticationError(DisagreementException):
    """Exception raised for authentication failures (e.g., invalid token)."""

    pass


class RateLimitError(HTTPException):
    """
    Exception raised when a rate limit is encountered.

    Attributes:
        retry_after (float): The number of seconds to wait before retrying.
        is_global (bool): Whether this is a global rate limit.
    """

    def __init__(
        self, response, message=None, *, retry_after: float, is_global: bool = False
    ):
        self.retry_after = retry_after
        self.is_global = is_global
        super().__init__(
            response,
            message
            or f"Rate limited. Retry after: {retry_after}s. Global: {is_global}",
        )


# Specific HTTP error exceptions


class NotFound(HTTPException):
    """Raised for 404 Not Found errors."""

    pass


class Forbidden(HTTPException):
    """Raised for 403 Forbidden errors."""

    pass


class AppCommandError(DisagreementException):
    """Base exception for application command related errors."""

    pass


class AppCommandOptionConversionError(AppCommandError):
    """Exception raised when an application command option fails to convert."""

    def __init__(
        self,
        message: str,
        option_name: Optional[str] = None,
        original_value: Any = None,
    ):
        self.option_name = option_name
        self.original_value = original_value
        full_message = message
        if option_name:
            full_message = f"Failed to convert option '{option_name}': {message}"
        if original_value is not None:
            full_message += f" (Original value: '{original_value}')"
        super().__init__(full_message)
