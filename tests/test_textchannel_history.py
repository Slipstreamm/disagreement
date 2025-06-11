import pytest

from disagreement.client import Client
from disagreement.models import TextChannel


@pytest.mark.asyncio
async def test_textchannel_history_delegates(monkeypatch):
    called = {}

    async def fake_pager(channel, *, limit=None, before=None, after=None):
        called["args"] = (channel, limit, before, after)
        if False:
            yield None

    monkeypatch.setattr("disagreement.utils.message_pager", fake_pager)
    client = Client.__new__(Client)
    channel = TextChannel({"id": "c", "type": 0}, client)

    hist = channel.history(limit=2, before="b")
    with pytest.raises(StopAsyncIteration):
        await hist.__anext__()

    assert called["args"] == (channel, 2, "b", None)
