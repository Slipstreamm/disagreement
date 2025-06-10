import asyncio
from unittest.mock import AsyncMock
import random

import pytest

from disagreement.gateway import GatewayClient, GatewayException
from disagreement.client import Client


class DummyHTTP:
    async def get_gateway_bot(self):
        return {"url": "ws://example"}

    async def _ensure_session(self):
        self._session = AsyncMock()
        self._session.ws_connect = AsyncMock()


class DummyDispatcher:
    async def dispatch(self, *_):
        pass


class DummyClient:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.application_id = None  # Mock application_id for Client.connect


@pytest.mark.asyncio
async def test_client_connect_backoff(monkeypatch):
    http = DummyHTTP()
    # Mock the GatewayClient's connect method to simulate failures and then success
    mock_gateway_connect = AsyncMock(
        side_effect=[GatewayException("boom"), GatewayException("boom"), None]
    )
    # Create a dummy client instance
    client = Client(
        token="test_token",
        intents=0,
        loop=asyncio.get_event_loop(),
        command_prefix="!",
        verbose=False,
        mention_replies=False,
        shard_count=None,
    )
    # Patch the internal _gateway attribute after client initialization
    # This ensures _initialize_gateway is called and _gateway is set
    await client._initialize_gateway()
    monkeypatch.setattr(client._gateway, "connect", mock_gateway_connect)

    # Mock wait_until_ready to prevent it from blocking the test
    monkeypatch.setattr(client, "wait_until_ready", AsyncMock())

    delays = []

    async def fake_sleep(d):
        delays.append(d)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    # Call the client's connect method, which contains the backoff logic
    await client.connect()

    # Assert that GatewayClient.connect was called the correct number of times
    assert mock_gateway_connect.call_count == 3
    # Assert the delays experienced due to exponential backoff
    assert delays == [5, 10]


@pytest.mark.asyncio
async def test_gateway_reconnect_backoff(monkeypatch):
    http = DummyHTTP()
    dispatcher = DummyDispatcher()
    client = DummyClient()
    gw = GatewayClient(
        http_client=http,
        event_dispatcher=dispatcher,
        token="t",
        intents=0,
        client_instance=client,
        max_retries=3,
        max_backoff=10.0,
    )

    connect_mock = AsyncMock(
        side_effect=[GatewayException("boom"), GatewayException("boom"), None]
    )
    monkeypatch.setattr(gw, "connect", connect_mock)

    delays = []

    async def fake_sleep(d):
        delays.append(d)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)

    await gw._reconnect()

    assert connect_mock.call_count == 3
    assert delays == [1.0, 2.0]
