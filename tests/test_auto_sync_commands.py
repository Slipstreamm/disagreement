import asyncio
from unittest.mock import AsyncMock

import pytest

from disagreement.client import Client
from disagreement.gateway import GatewayClient
from disagreement.event_dispatcher import EventDispatcher


class DummyHTTP:
    pass


class DummyUser:
    username = "u"
    discriminator = "0001"


@pytest.mark.asyncio
async def test_auto_sync_on_ready(monkeypatch):
    client = Client(token="t", application_id="123")
    http = DummyHTTP()
    dispatcher = EventDispatcher(client)
    gw = GatewayClient(
        http_client=http,
        event_dispatcher=dispatcher,
        token="t",
        intents=0,
        client_instance=client,
    )
    monkeypatch.setattr(client, "parse_user", lambda d: DummyUser())
    monkeypatch.setattr(gw._dispatcher, "dispatch", AsyncMock())
    sync_mock = AsyncMock()
    monkeypatch.setattr(client, "sync_application_commands", sync_mock)

    data = {
        "t": "READY",
        "s": 1,
        "d": {
            "session_id": "s1",
            "resume_gateway_url": "url",
            "application": {"id": "123"},
            "user": {"id": "1"},
        },
    }

    await gw._handle_dispatch(data)
    await asyncio.sleep(0)
    sync_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_auto_sync_disabled(monkeypatch):
    client = Client(token="t", application_id="123", sync_commands_on_ready=False)
    http = DummyHTTP()
    dispatcher = EventDispatcher(client)
    gw = GatewayClient(
        http_client=http,
        event_dispatcher=dispatcher,
        token="t",
        intents=0,
        client_instance=client,
    )
    monkeypatch.setattr(client, "parse_user", lambda d: DummyUser())
    monkeypatch.setattr(gw._dispatcher, "dispatch", AsyncMock())
    sync_mock = AsyncMock()
    monkeypatch.setattr(client, "sync_application_commands", sync_mock)

    data = {
        "t": "READY",
        "s": 1,
        "d": {
            "session_id": "s1",
            "resume_gateway_url": "url",
            "application": {"id": "123"},
            "user": {"id": "1"},
        },
    }

    await gw._handle_dispatch(data)
    await asyncio.sleep(0)
    sync_mock.assert_not_called()
