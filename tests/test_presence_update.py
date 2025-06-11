import pytest
from unittest.mock import AsyncMock

from disagreement.client import Client
from disagreement.models import Game
from disagreement.errors import DisagreementException


from unittest.mock import MagicMock


class DummyGateway(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_presence = AsyncMock()


@pytest.mark.asyncio
async def test_change_presence_passes_arguments():
    client = Client(token="t")
    client._gateway = DummyGateway()
    game = Game("hi")
    await client.change_presence(status="idle", activity=game)

    client._gateway.update_presence.assert_awaited_once_with(
        status="idle", activity=game, since=0, afk=False
    )


@pytest.mark.asyncio
async def test_change_presence_when_closed():
    client = Client(token="t")
    client._closed = True
    with pytest.raises(DisagreementException):
        await client.change_presence(status="online")
