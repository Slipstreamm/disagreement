import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.http import HTTPClient
from disagreement.client import Client


@pytest.mark.asyncio
async def test_get_guild_widget_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={})
    await http.get_guild_widget("1")
    http.request.assert_called_once_with("GET", "/guilds/1/widget")


@pytest.mark.asyncio
async def test_edit_guild_widget_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={})
    payload = {"enabled": True}
    await http.edit_guild_widget("1", payload)
    http.request.assert_called_once_with("PATCH", "/guilds/1/widget", payload=payload)


@pytest.mark.asyncio
async def test_client_fetch_widget_returns_data():
    http = SimpleNamespace(get_guild_widget=AsyncMock(return_value={"enabled": True}))
    client = Client.__new__(Client)
    client._http = http
    client._closed = False

    data = await client.fetch_widget("1")

    http.get_guild_widget.assert_awaited_once_with("1")
    assert data == {"enabled": True}


@pytest.mark.asyncio
async def test_client_edit_widget_returns_data():
    http = SimpleNamespace(edit_guild_widget=AsyncMock(return_value={"enabled": False}))
    client = Client.__new__(Client)
    client._http = http
    client._closed = False

    payload = {"enabled": False}
    data = await client.edit_widget("1", payload)

    http.edit_guild_widget.assert_awaited_once_with("1", payload)
    assert data == {"enabled": False}
