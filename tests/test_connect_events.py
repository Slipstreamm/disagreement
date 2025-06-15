import asyncio
import pytest
from unittest.mock import AsyncMock

from disagreement.shard_manager import ShardManager
from disagreement.event_dispatcher import EventDispatcher


class DummyGateway:
    def __init__(self, *args, **kwargs):
        self.connect = AsyncMock()
        self.close = AsyncMock()

        dispatcher = kwargs.get("event_dispatcher")
        shard_id = kwargs.get("shard_id")

        async def emit_connect():
            await dispatcher.dispatch("CONNECT", {"shard_id": shard_id})

        async def emit_close():
            await dispatcher.dispatch("DISCONNECT", {"shard_id": shard_id})

        self.connect.side_effect = emit_connect
        self.close.side_effect = emit_close


class DummyClient:
    def __init__(self):
        self._http = object()
        self._event_dispatcher = EventDispatcher(self)
        self.token = "t"
        self.intents = 0
        self.verbose = False
        self.gateway_max_retries = 5
        self.gateway_max_backoff = 60.0


@pytest.mark.asyncio
async def test_connect_disconnect_events(monkeypatch):
    monkeypatch.setattr("disagreement.shard_manager.GatewayClient", DummyGateway)
    client = DummyClient()
    manager = ShardManager(client, shard_count=1)

    events: list[tuple[str, int | None]] = []

    async def on_connect(info):
        events.append(("connect", info.get("shard_id")))

    async def on_disconnect(info):
        events.append(("disconnect", info.get("shard_id")))

    client._event_dispatcher.register("CONNECT", on_connect)
    client._event_dispatcher.register("DISCONNECT", on_disconnect)

    await manager.start()
    await manager.close()

    assert ("connect", 0) in events
    assert ("disconnect", 0) in events
