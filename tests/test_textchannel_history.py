import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.client import Client
from disagreement.models import TextChannel, Message


@pytest.mark.asyncio
async def test_textchannel_history_paginates():
    first_page = [
        {
            "id": "3",
            "channel_id": "c",
            "author": {"id": "1", "username": "u", "discriminator": "0001"},
            "content": "m3",
            "timestamp": "t",
        },
        {
            "id": "2",
            "channel_id": "c",
            "author": {"id": "1", "username": "u", "discriminator": "0001"},
            "content": "m2",
            "timestamp": "t",
        },
    ]
    second_page = [
        {
            "id": "1",
            "channel_id": "c",
            "author": {"id": "1", "username": "u", "discriminator": "0001"},
            "content": "m1",
            "timestamp": "t",
        }
    ]
    http = SimpleNamespace(request=AsyncMock(side_effect=[first_page, second_page]))
    client = Client.__new__(Client)
    client._http = http
    channel = TextChannel({"id": "c", "type": 0}, client)

    messages = []
    async for msg in channel.history(limit=3):
        messages.append(msg)

    assert len(messages) == 3
    assert all(isinstance(m, Message) for m in messages)
    http.request.assert_any_call("GET", "/channels/c/messages", params={"limit": 3})
    http.request.assert_any_call(
        "GET", "/channels/c/messages", params={"limit": 1, "before": "2"}
    )


@pytest.mark.asyncio
async def test_textchannel_history_before_param():
    http = SimpleNamespace(request=AsyncMock(return_value=[]))
    client = Client.__new__(Client)
    client._http = http
    channel = TextChannel({"id": "c", "type": 0}, client)

    messages = [m async for m in channel.history(limit=1, before="b")]

    assert messages == []
    http.request.assert_called_once_with(
        "GET", "/channels/c/messages", params={"limit": 1, "before": "b"}
    )
