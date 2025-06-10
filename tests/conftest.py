import pytest
from unittest.mock import AsyncMock

from disagreement.interactions import Interaction
from disagreement.enums import InteractionType
from disagreement.models import Message


class DummyHTTP:
    def __init__(self):
        self.create_interaction_response = AsyncMock()
        self.create_followup_message = AsyncMock(
            return_value={
                "id": "123",
                "channel_id": "c",
                "author": {"id": "1", "username": "u", "discriminator": "0001"},
                "content": "hi",
                "timestamp": "t",
            }
        )
        self.edit_original_interaction_response = AsyncMock(return_value={"id": "123"})
        self.edit_followup_message = AsyncMock(
            return_value={
                "id": "123",
                "channel_id": "c",
                "author": {"id": "1", "username": "u", "discriminator": "0001"},
                "content": "hi",
                "timestamp": "t",
            }
        )


class DummyBot:
    def __init__(self):
        self._http = DummyHTTP()
        self.application_id = "app123"
        self._guilds = {}
        self._channels = {}

    def get_guild(self, gid):
        return self._guilds.get(gid)

    async def fetch_channel(self, cid):
        return self._channels.get(cid)


class DummyCommandHTTP:
    def __init__(self):
        self.edit_message = AsyncMock(return_value={"id": "321", "channel_id": "c"})


class DummyCommandBot:
    def __init__(self):
        self._http = DummyCommandHTTP()

    async def edit_message(self, channel_id, message_id, *, content=None, **kwargs):
        return await self._http.edit_message(
            channel_id, message_id, {"content": content, **kwargs}
        )


class DummyClient:
    pass


class DummyInteraction:
    data = None


@pytest.fixture()
def dummy_bot():
    return DummyBot()


@pytest.fixture()
def interaction(dummy_bot):
    data = {
        "id": "1",
        "application_id": dummy_bot.application_id,
        "type": InteractionType.APPLICATION_COMMAND.value,
        "token": "tok",
        "version": 1,
    }
    return Interaction(data, client_instance=dummy_bot)


@pytest.fixture()
def command_bot():
    return DummyCommandBot()


@pytest.fixture()
def message(command_bot):
    message_data = {
        "id": "1",
        "channel_id": "c",
        "author": {"id": "2", "username": "u", "discriminator": "0001"},
        "content": "hi",
        "timestamp": "t",
    }
    return Message(message_data, client_instance=command_bot)


@pytest.fixture()
def dummy_client():
    return DummyClient()


@pytest.fixture()
def basic_interaction():
    return DummyInteraction()
