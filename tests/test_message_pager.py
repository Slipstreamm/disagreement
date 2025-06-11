import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.client import Client
from disagreement.models import TextChannel
from disagreement.utils import message_pager


@pytest.mark.asyncio
async def test_message_pager_fetches_until_empty():
    calls = [
        [
            {
                "id": "1",
                "channel_id": "c",
                "author": {"id": "2", "username": "u", "discriminator": "0001"},
                "content": "hi",
                "timestamp": "t",
            }
        ],
        [],
    ]
    http = SimpleNamespace(request=AsyncMock(side_effect=calls))
    client = Client.__new__(Client)
    client._http = http
    from disagreement.models import Message

    client.parse_message = lambda d: Message(d, client_instance=client)
    channel = TextChannel({"id": "c", "type": 0}, client)

    messages = []
    async for m in message_pager(channel):
        messages.append(m)

    assert len(messages) == 1
    http.request.assert_awaited()
