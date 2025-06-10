import pytest

from disagreement.event_dispatcher import EventDispatcher
from disagreement.models import PresenceUpdate, TypingStart


@pytest.mark.asyncio
async def test_presence_and_typing_parsing(dummy_client):
    dispatcher = EventDispatcher(dummy_client)
    events = {}

    async def on_presence(presence):
        events["presence"] = presence

    async def on_typing(typing):
        events["typing"] = typing

    dispatcher.register("PRESENCE_UPDATE", on_presence)
    dispatcher.register("TYPING_START", on_typing)

    presence_data = {
        "user": {"id": "1", "username": "u", "discriminator": "0001"},
        "guild_id": "g",
        "status": "online",
        "activities": [],
        "client_status": {},
    }
    typing_data = {
        "channel_id": "c",
        "user_id": "1",
        "timestamp": 123,
    }
    await dispatcher.dispatch("PRESENCE_UPDATE", presence_data)
    await dispatcher.dispatch("TYPING_START", typing_data)

    assert isinstance(events.get("presence"), PresenceUpdate)
    assert events["presence"].status == "online"
    assert isinstance(events.get("typing"), TypingStart)
    assert events["typing"].channel_id == "c"
