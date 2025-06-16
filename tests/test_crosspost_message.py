import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.http import HTTPClient
from disagreement.client import Client
from disagreement.models import Message


@pytest.mark.asyncio
async def test_http_crosspost_message_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={"id": "m"})
    data = await http.crosspost_message("c", "m")
    http.request.assert_called_once_with(
        "POST",
        "/channels/c/messages/m/crosspost",
    )
    assert data == {"id": "m"}


@pytest.mark.asyncio
async def test_message_crosspost_returns_message():
    payload = {
        "id": "2",
        "channel_id": "1",
        "author": {"id": "3", "username": "u", "discriminator": "0001"},
        "content": "hi",
        "timestamp": "t",
    }
    http = SimpleNamespace(crosspost_message=AsyncMock(return_value=payload))
    client = Client.__new__(Client)
    client._http = http
    client.parse_message = lambda d: Message(d, client_instance=client)
    message = Message(payload, client_instance=client)

    new_msg = await message.crosspost()

    http.crosspost_message.assert_awaited_once_with("1", "2")
    assert isinstance(new_msg, Message)
    assert new_msg._client is client
