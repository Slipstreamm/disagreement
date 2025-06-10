import pytest
from unittest.mock import AsyncMock

from disagreement.client import Client
from disagreement.http import HTTPClient
from disagreement.models import Attachment, File


@pytest.mark.asyncio
async def test_http_send_message_includes_attachments():
    http = HTTPClient(token="t")
    http.request = AsyncMock(
        return_value={
            "id": "1",
            "channel_id": "c",
            "author": {"id": "2", "username": "u", "discriminator": "0001"},
            "content": "hi",
            "timestamp": "t",
        }
    )
    await http.send_message("c", "hi", attachments=[{"id": 1}])
    http.request.assert_called_once_with(
        "POST",
        "/channels/c/messages",
        payload={"content": "hi", "attachments": [{"id": 1}]},
    )


@pytest.mark.asyncio
async def test_http_send_message_with_files_uses_formdata():
    http = HTTPClient(token="t")
    http.request = AsyncMock(
        return_value={
            "id": "1",
            "channel_id": "c",
            "author": {"id": "2", "username": "u", "discriminator": "0001"},
            "content": "hi",
            "timestamp": "t",
        }
    )
    await http.send_message("c", "hi", files=[File("f.txt", b"data")])
    args, kwargs = http.request.call_args
    assert kwargs["is_json"] is False


@pytest.mark.asyncio
async def test_client_send_message_passes_attachments():
    client = Client(token="t")
    client._http.send_message = AsyncMock(
        return_value={
            "id": "1",
            "channel_id": "c",
            "author": {"id": "2", "username": "u", "discriminator": "0001"},
            "content": "hi",
            "timestamp": "t",
            "attachments": [{"id": "1", "filename": "f.txt"}],
        }
    )
    msg = await client.send_message("c", "hi", attachments=[{"id": "1"}])
    client._http.send_message.assert_awaited_once()
    kwargs = client._http.send_message.call_args.kwargs
    assert kwargs["attachments"] == [{"id": "1"}]
    assert isinstance(msg.attachments[0], Attachment)


@pytest.mark.asyncio
async def test_client_send_message_passes_files():
    client = Client(token="t")
    client._http.send_message = AsyncMock(
        return_value={
            "id": "1",
            "channel_id": "c",
            "author": {"id": "2", "username": "u", "discriminator": "0001"},
            "content": "hi",
            "timestamp": "t",
        }
    )
    await client.send_message("c", "hi", files=[File("f.txt", b"data")])
    client._http.send_message.assert_awaited_once()
    kwargs = client._http.send_message.call_args.kwargs
    assert kwargs["files"][0].filename == "f.txt"
