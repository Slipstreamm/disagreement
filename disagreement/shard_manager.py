# disagreement/shard_manager.py

"""Sharding utilities for managing multiple gateway connections."""

from __future__ import annotations

import asyncio
from typing import List, TYPE_CHECKING

from .gateway import GatewayClient

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from .client import Client


class Shard:
    """Represents a single gateway shard."""

    def __init__(self, shard_id: int, shard_count: int, gateway: GatewayClient) -> None:
        self.id: int = shard_id
        self.count: int = shard_count
        self.gateway: GatewayClient = gateway

    async def connect(self) -> None:
        """Connects this shard's gateway."""
        await self.gateway.connect()

    async def close(self) -> None:
        """Closes this shard's gateway."""
        await self.gateway.close()


class ShardManager:
    """Manages multiple :class:`Shard` instances."""

    def __init__(self, client: "Client", shard_count: int) -> None:
        self.client: "Client" = client
        self.shard_count: int = shard_count
        self.shards: List[Shard] = []

    def _create_shards(self) -> None:
        if self.shards:
            return
        for shard_id in range(self.shard_count):
            gateway = GatewayClient(
                http_client=self.client._http,
                event_dispatcher=self.client._event_dispatcher,
                token=self.client.token,
                intents=self.client.intents,
                client_instance=self.client,
                verbose=self.client.verbose,
                shard_id=shard_id,
                shard_count=self.shard_count,
                max_retries=self.client.gateway_max_retries,
                max_backoff=self.client.gateway_max_backoff,
            )
            self.shards.append(Shard(shard_id, self.shard_count, gateway))

    async def start(self) -> None:
        """Starts all shards."""
        self._create_shards()
        await asyncio.gather(*(s.connect() for s in self.shards))

    async def close(self) -> None:
        """Closes all shards."""
        await asyncio.gather(*(s.close() for s in self.shards))
        self.shards.clear()
