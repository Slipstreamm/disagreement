import pytest
from unittest.mock import AsyncMock

from disagreement.client import Client
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

    await client.change_presence(status="idle", activity_name="hi", activity_type=0)

    client._gateway.update_presence.assert_awaited_once_with(
        status="idle", activity_name="hi", activity_type=0, since=0, afk=False
    )


@pytest.mark.asyncio
async def test_change_presence_when_closed():
    client = Client(token="t")
    client._closed = True
    with pytest.raises(DisagreementException):
        await client.change_presence(status="online")
