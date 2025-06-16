import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.http import HTTPClient
from disagreement.client import Client
from disagreement.models import Invite


@pytest.mark.asyncio
async def test_http_get_invite_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={"code": "abc"})

    result = await http.get_invite("abc")

    http.request.assert_called_once_with("GET", "/invites/abc")
    assert result == {"code": "abc"}


@pytest.mark.asyncio
async def test_client_fetch_invite_returns_invite():
    http = SimpleNamespace(get_invite=AsyncMock(return_value={"code": "abc"}))
    client = Client.__new__(Client)
    client._http = http
    client._closed = False

    invite = await client.fetch_invite("abc")

    http.get_invite.assert_awaited_once_with("abc")
    assert isinstance(invite, Invite)
