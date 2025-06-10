import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.client import Client
from disagreement.models import TextChannel


@pytest.mark.asyncio
async def test_textchannel_purge_calls_bulk_delete():
    http = SimpleNamespace(
        request=AsyncMock(return_value=[{"id": "1"}, {"id": "2"}]),
        bulk_delete_messages=AsyncMock(),
    )
    client = Client.__new__(Client)
    client._http = http
    client._messages = {}

    channel = TextChannel({"id": "c", "type": 0}, client)

    deleted = await channel.purge(2)

    http.request.assert_called_once_with(
        "GET", "/channels/c/messages", params={"limit": 2}
    )
    http.bulk_delete_messages.assert_awaited_once_with("c", ["1", "2"])
    assert deleted == ["1", "2"]


@pytest.mark.asyncio
async def test_textchannel_purge_before_param():
    http = SimpleNamespace(
        request=AsyncMock(return_value=[]),
        bulk_delete_messages=AsyncMock(),
    )
    client = Client.__new__(Client)
    client._http = http
    client._messages = {}

    channel = TextChannel({"id": "c", "type": 0}, client)

    deleted = await channel.purge(1, before="b")

    http.request.assert_called_once_with(
        "GET", "/channels/c/messages", params={"limit": 1, "before": "b"}
    )
    http.bulk_delete_messages.assert_not_awaited()
    assert deleted == []
