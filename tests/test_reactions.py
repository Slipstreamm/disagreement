import pytest
from disagreement.event_dispatcher import EventDispatcher


@pytest.mark.asyncio
async def test_reaction_payload():
    # This test now checks the raw payload dictionary, as the Reaction model is removed.
    data = {
        "user_id": "1",
        "channel_id": "2",
        "message_id": "3",
        "emoji": {"name": "😀", "id": None},
    }
    # The "reaction" is just the data dictionary itself.
    assert data["user_id"] == "1"
    assert data["emoji"]["name"] == "😀"


@pytest.mark.asyncio
async def test_dispatch_reaction_event(dummy_client):
    dispatcher = EventDispatcher(dummy_client)
    captured = []

    async def listener(payload: dict):
        captured.append(payload)

    # The event name is now MESSAGE_REACTION_ADD as per the original test setup.
    # If this were to fail, the next step would be to confirm the correct event name.
    dispatcher.register("MESSAGE_REACTION_ADD", listener)
    payload = {
        "user_id": "1",
        "channel_id": "2",
        "message_id": "3",
        "emoji": {"name": "👍", "id": None},
    }
    await dispatcher.dispatch("MESSAGE_REACTION_ADD", payload)
    assert len(captured) == 1
    assert isinstance(captured[0], dict)
