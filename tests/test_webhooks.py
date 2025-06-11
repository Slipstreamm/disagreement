import pytest
from unittest.mock import AsyncMock

from disagreement.http import HTTPClient


@pytest.mark.asyncio
async def test_create_followup_message_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock()
    payload = {"content": "hello"}
    await http.create_followup_message("app_id", "token", payload)
    http.request.assert_called_once_with(
        "POST",
        f"/webhooks/app_id/token",
        payload=payload,
        use_auth_header=False,
    )


@pytest.mark.asyncio
async def test_edit_followup_message_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock()
    payload = {"content": "new content"}
    await http.edit_followup_message("app_id", "token", "123", payload)
    http.request.assert_called_once_with(
        "PATCH",
        f"/webhooks/app_id/token/messages/123",
        payload=payload,
        use_auth_header=False,
    )


@pytest.mark.asyncio
async def test_delete_followup_message_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock()
    await http.delete_followup_message("app_id", "token", "456")
    http.request.assert_called_once_with(
        "DELETE",
        f"/webhooks/app_id/token/messages/456",
        use_auth_header=False,
    )


@pytest.mark.asyncio
async def test_create_webhook_returns_model_and_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={"id": "1"})
    payload = {"name": "wh"}
    webhook = await http.create_webhook("123", payload)
    http.request.assert_called_once_with(
        "POST",
        "/channels/123/webhooks",
        payload=payload,
    )
    from disagreement.models import Webhook

    assert isinstance(webhook, Webhook)


@pytest.mark.asyncio
async def test_edit_webhook_returns_model_and_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={"id": "1"})
    payload = {"name": "rename"}
    webhook = await http.edit_webhook("1", payload)
    http.request.assert_called_once_with(
        "PATCH",
        "/webhooks/1",
        payload=payload,
    )
    from disagreement.models import Webhook

    assert isinstance(webhook, Webhook)


@pytest.mark.asyncio
async def test_delete_webhook_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock()
    await http.delete_webhook("1")
    http.request.assert_called_once_with(
        "DELETE",
        "/webhooks/1",
    )


@pytest.mark.asyncio
async def test_client_create_webhook_returns_model():
    from types import SimpleNamespace
    from disagreement.client import Client
    from disagreement.models import Webhook

    http = SimpleNamespace(create_webhook=AsyncMock(return_value={"id": "1"}))
    client = Client.__new__(Client)
    client._http = http
    client._closed = False
    client._webhooks = {}

    webhook = await client.create_webhook("123", {"name": "wh"})

    http.create_webhook.assert_awaited_once_with("123", {"name": "wh"})
    assert isinstance(webhook, Webhook)
    assert client._webhooks["1"] is webhook


@pytest.mark.asyncio
async def test_client_edit_webhook_returns_model():
    from types import SimpleNamespace
    from disagreement.client import Client
    from disagreement.models import Webhook

    http = SimpleNamespace(edit_webhook=AsyncMock(return_value={"id": "1"}))
    client = Client.__new__(Client)
    client._http = http
    client._closed = False
    client._webhooks = {}

    webhook = await client.edit_webhook("1", {"name": "rename"})

    http.edit_webhook.assert_awaited_once_with("1", {"name": "rename"})
    assert isinstance(webhook, Webhook)
    assert client._webhooks["1"] is webhook


@pytest.mark.asyncio
async def test_client_delete_webhook_calls_http():
    from types import SimpleNamespace
    from disagreement.client import Client

    http = SimpleNamespace(delete_webhook=AsyncMock())
    client = Client.__new__(Client)
    client._http = http
    client._closed = False

    await client.delete_webhook("1")

    http.delete_webhook.assert_awaited_once_with("1")


def test_webhook_from_url_parses_id_and_token():
    from disagreement.models import Webhook

    url = "https://discord.com/api/webhooks/123/token"
    webhook = Webhook.from_url(url)

    assert webhook.id == "123"
    assert webhook.token == "token"
    assert webhook.url == url


@pytest.mark.asyncio
async def test_execute_webhook_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={"id": "1"})
    await http.execute_webhook("1", "tok", content="hi")
    http.request.assert_called_once_with(
        "POST",
        "/webhooks/1/tok",
        payload={"content": "hi"},
        use_auth_header=False,
    )


@pytest.mark.asyncio
async def test_webhook_send_uses_http():
    from types import SimpleNamespace
    from disagreement.client import Client
    from disagreement.models import Webhook, Message

    http = SimpleNamespace(
        execute_webhook=AsyncMock(
            return_value={
                "id": "2",
                "channel_id": "c",
                "author": {"id": "1", "username": "u", "discriminator": "0001"},
                "content": "hi",
                "timestamp": "t",
            }
        )
    )
    client = Client.__new__(Client)
    client._http = http
    client._messages = {}
    client._webhooks = {}

    webhook = Webhook({"id": "1", "token": "tok"}, client_instance=client)

    msg = await webhook.send(content="hi")

    http.execute_webhook.assert_awaited_once()
    assert isinstance(msg, Message)
