import pytest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.client import Client


@pytest.mark.asyncio
async def test_client_records_start_time(monkeypatch):
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)

    monkeypatch.setattr("disagreement.client.utcnow", lambda: start)

    client = Client(token="t")
    monkeypatch.setattr(client, "_initialize_gateway", AsyncMock())
    client._gateway = SimpleNamespace(connect=AsyncMock())
    monkeypatch.setattr(client, "wait_until_ready", AsyncMock())

    assert client.start_time is None
    await client.connect()
    assert client.start_time == start


@pytest.mark.asyncio
async def test_client_uptime(monkeypatch):
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    end = start + timedelta(seconds=5)
    times = [start, end]

    def fake_now():
        return times.pop(0)

    monkeypatch.setattr("disagreement.client.utcnow", fake_now)

    client = Client(token="t")
    monkeypatch.setattr(client, "_initialize_gateway", AsyncMock())
    client._gateway = SimpleNamespace(connect=AsyncMock())
    monkeypatch.setattr(client, "wait_until_ready", AsyncMock())

    await client.connect()
    assert client.uptime() == timedelta(seconds=5)
