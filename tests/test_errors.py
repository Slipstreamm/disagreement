import pytest

from disagreement.errors import (
    HTTPException,
    RateLimitError,
    AppCommandOptionConversionError,
)


def test_http_exception_message():
    exc = HTTPException(message="Bad", status=400)
    assert str(exc) == "HTTP 400: Bad"


def test_rate_limit_error_inherits_httpexception():
    exc = RateLimitError(response=None, retry_after=1.0, is_global=True)
    assert isinstance(exc, HTTPException)
    assert "Rate limited" in str(exc)


def test_app_command_option_conversion_error():
    exc = AppCommandOptionConversionError("bad", option_name="opt", original_value="x")
    assert "opt" in str(exc) and "x" in str(exc)
