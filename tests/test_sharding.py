import pytest
from unittest.mock import AsyncMock

from disagreement.shard_manager import ShardManager
from disagreement.client import Client, AutoShardedClient
from disagreement.event_dispatcher import EventDispatcher


class DummyGateway:
    def __init__(self, *args, **kwargs):
        self.connect = AsyncMock()
        self.close = AsyncMock()

        dispatcher = kwargs.get("event_dispatcher")
        shard_id = kwargs.get("shard_id")

        async def emit_connect():
            await dispatcher.dispatch("SHARD_CONNECT", {"shard_id": shard_id})

        async def emit_close():
            await dispatcher.dispatch("SHARD_DISCONNECT", {"shard_id": shard_id})

        async def emit_resume():
            await dispatcher.dispatch("SHARD_RESUME", {"shard_id": shard_id})

        self.connect.side_effect = emit_connect
        self.close.side_effect = emit_close
        self.resume = AsyncMock(side_effect=emit_resume)


class DummyClient:
    def __init__(self):
        self._http = object()
        self._event_dispatcher = EventDispatcher(self)
        self.token = "t"
        self.intents = 0
        self.verbose = False
        self.gateway_max_retries = 5
        self.gateway_max_backoff = 60.0


def test_shard_manager_creates_shards(monkeypatch):
    monkeypatch.setattr("disagreement.shard_manager.GatewayClient", DummyGateway)
    client = DummyClient()
    manager = ShardManager(client, shard_count=3)
    assert len(manager.shards) == 0
    manager._create_shards()
    assert len(manager.shards) == 3


@pytest.mark.asyncio
async def test_shard_manager_start_and_close(monkeypatch):
    monkeypatch.setattr("disagreement.shard_manager.GatewayClient", DummyGateway)
    client = DummyClient()
    manager = ShardManager(client, shard_count=2)
    await manager.start()
    for shard in manager.shards:
        shard.gateway.connect.assert_awaited_once()
    await manager.close()
    for shard in manager.shards:
        shard.gateway.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_client_uses_shard_manager(monkeypatch):
    dummy_manager = AsyncMock()
    monkeypatch.setattr("disagreement.client.ShardManager", lambda c, n: dummy_manager)
    c = Client(token="x", shard_count=2)
    monkeypatch.setattr(c, "wait_until_ready", AsyncMock())
    await c.connect()
    dummy_manager.start.assert_awaited_once()


@pytest.mark.asyncio
async def test_auto_sharded_client_fetches_count(monkeypatch):
    class DummyHTTP:
        async def get_gateway_bot(self):
            return {"shards": 4}

    dummy_manager = AsyncMock()
    monkeypatch.setattr("disagreement.client.ShardManager", lambda c, n: dummy_manager)
    c = AutoShardedClient(token="x")
    c._http = DummyHTTP()
    monkeypatch.setattr(c, "wait_until_ready", AsyncMock())
    await c.connect()
    dummy_manager.start.assert_awaited_once()
    assert c.shard_count == 4


@pytest.mark.asyncio
async def test_shard_events_emitted(monkeypatch):
    monkeypatch.setattr("disagreement.shard_manager.GatewayClient", DummyGateway)

    client = DummyClient()
    manager = ShardManager(client, shard_count=1)

    events: list[tuple[str, int | None]] = []

    async def on_connect(info):
        events.append(("connect", info.get("shard_id")))

    async def on_disconnect(info):
        events.append(("disconnect", info.get("shard_id")))

    async def on_resume(info):
        events.append(("resume", info.get("shard_id")))

    client._event_dispatcher.register("SHARD_CONNECT", on_connect)
    client._event_dispatcher.register("SHARD_DISCONNECT", on_disconnect)
    client._event_dispatcher.register("SHARD_RESUME", on_resume)

    await manager.start()
    await manager.shards[0].gateway.resume()
    await manager.close()

    assert ("connect", 0) in events
    assert ("disconnect", 0) in events
    assert ("resume", 0) in events
