import asyncio

import pytest

from disagreement.event_dispatcher import EventDispatcher


class DummyClient:
    def __init__(self):
        self.parsed = {}

    def parse_message(self, data):
        self.parsed["message"] = True
        return data

    def parse_guild(self, data):
        self.parsed["guild"] = True
        return data

    def parse_channel(self, data):
        self.parsed["channel"] = True
        return data


@pytest.mark.asyncio
async def test_dispatch_calls_listener():
    client = DummyClient()
    dispatcher = EventDispatcher(client)
    called = {}

    async def listener(payload):
        called["data"] = payload

    dispatcher.register("MESSAGE_CREATE", listener)
    await dispatcher.dispatch("MESSAGE_CREATE", {"id": 1})
    assert called["data"] == {"id": 1}
    assert client.parsed.get("message")


@pytest.mark.asyncio
async def test_dispatch_listener_no_args():
    client = DummyClient()
    dispatcher = EventDispatcher(client)
    called = False

    async def listener():
        nonlocal called
        called = True

    dispatcher.register("GUILD_CREATE", listener)
    await dispatcher.dispatch("GUILD_CREATE", {"id": 123})
    assert called


@pytest.mark.asyncio
async def test_unregister_listener():
    client = DummyClient()
    dispatcher = EventDispatcher(client)
    called = False

    async def listener(_):
        nonlocal called
        called = True

    dispatcher.register("MESSAGE_CREATE", listener)
    dispatcher.unregister("MESSAGE_CREATE", listener)
    await dispatcher.dispatch("MESSAGE_CREATE", {"id": 1})
    assert not called
