import pytest
import aiohttp
from unittest.mock import MagicMock, patch
from disagreement.errors import (
    HTTPException,
    RateLimitError,
    AppCommandOptionConversionError,
    Forbidden,
    NotFound,
    UnknownAccount,
    MaximumNumberOfGuildsReached,
)
from disagreement.http import HTTPClient


# A fixture to provide an HTTPClient with a mocked session
@pytest.fixture
def http_client():
    # Using a real session and patching the request method is more robust
    client = HTTPClient(token="fake_token")
    yield client

    # Cleanup: close the session after the test
    # This requires making the fixture async or running this in an event loop
    async def close_session():
        if client._session:
            await client.close()

    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.run_until_complete(close_session())
    except RuntimeError:
        asyncio.run(close_session())


# Mock aiohttp response
class MockAiohttpResponse:
    def __init__(self, status, json_data, headers=None):
        self.status = status
        self._json_data = json_data
        self.headers = headers or {"Content-Type": "application/json"}

    async def json(self):
        return self._json_data

    async def text(self):
        return str(self._json_data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_code, error_message, expected_exception",
    [
        (10001, "Unknown account", UnknownAccount),
        (30001, "Maximum number of guilds reached", MaximumNumberOfGuildsReached),
    ],
)
async def test_error_code_mapping_raises_correct_exception(
    http_client, error_code, error_message, expected_exception
):
    """
    Tests if the HTTP client correctly raises a specific exception
    based on the Discord error code.
    """
    mock_response = MockAiohttpResponse(
        status=400, json_data={"code": error_code, "message": error_message}
    )

    # Patch the session object to control the response
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session_instance = mock_session_class.return_value
        mock_session_instance.request.return_value = mock_response

        # Assert that the correct exception is raised
        with pytest.raises(expected_exception) as excinfo:
            await http_client.request("GET", "/test-endpoint")

    # Optionally, check the exception details
    assert excinfo.value.status == 400
    assert excinfo.value.error_code == error_code
    assert error_message in str(excinfo.value)


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


def test_specific_http_exceptions():
    not_found = NotFound(message="missing", status=404)
    forbidden = Forbidden(message="forbidden", status=403)
    assert isinstance(not_found, HTTPException)
    assert isinstance(forbidden, HTTPException)
