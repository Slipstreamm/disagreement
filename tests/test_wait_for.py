import asyncio

import pytest  # pylint: disable=import-error

from disagreement.client import Client


@pytest.mark.asyncio
async def test_wait_for_resolves_on_event():
    client = Client(token="t")

    async def dispatch_event():
        await asyncio.sleep(0.05)
        data = {
            "id": "42",
            "channel_id": "c",
            "author": {"id": "1", "username": "u", "discriminator": "0001"},
            "content": "hello",
            "timestamp": "t",
        }
        await client._event_dispatcher.dispatch("MESSAGE_CREATE", data)

    asyncio.create_task(dispatch_event())
    message = await client.wait_for(
        "MESSAGE_CREATE", check=lambda m: m.id == "42", timeout=1
    )

    assert message.content == "hello"


@pytest.mark.asyncio
async def test_wait_for_timeout():
    client = Client(token="t")
    with pytest.raises(asyncio.TimeoutError):
        await client.wait_for("MESSAGE_CREATE", timeout=0.1)
