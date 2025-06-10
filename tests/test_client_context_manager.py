import asyncio
import pytest
from unittest.mock import AsyncMock

from disagreement.client import Client


@pytest.mark.asyncio
async def test_client_async_context_closes(monkeypatch):
    client = Client(token="t")
    monkeypatch.setattr(client, "connect", AsyncMock())
    monkeypatch.setattr(client._http, "close", AsyncMock())

    async with client:
        client.connect.assert_awaited_once()

    client._http.close.assert_awaited_once()
    assert client.is_closed()


@pytest.mark.asyncio
async def test_client_async_context_closes_on_exception(monkeypatch):
    client = Client(token="t")
    monkeypatch.setattr(client, "connect", AsyncMock())
    monkeypatch.setattr(client._http, "close", AsyncMock())

    with pytest.raises(ValueError):
        async with client:
            raise ValueError("boom")

    client.connect.assert_awaited_once()
    client._http.close.assert_awaited_once()
    assert client.is_closed()
