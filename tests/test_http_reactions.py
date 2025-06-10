import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.client import Client
from disagreement.errors import DisagreementException
from disagreement.models import User


@pytest.mark.asyncio
async def test_create_reaction_calls_http():
    http = SimpleNamespace(create_reaction=AsyncMock())
    client = Client.__new__(Client)
    client._http = http
    client._closed = False

    await client.create_reaction("1", "2", "😀")

    http.create_reaction.assert_called_once_with("1", "2", "😀")


@pytest.mark.asyncio
async def test_create_reaction_closed():
    http = SimpleNamespace(create_reaction=AsyncMock())
    client = Client.__new__(Client)
    client._http = http
    client._closed = True

    with pytest.raises(DisagreementException):
        await client.create_reaction("1", "2", "😀")


@pytest.mark.asyncio
async def test_delete_reaction_calls_http():
    http = SimpleNamespace(delete_reaction=AsyncMock())
    client = Client.__new__(Client)
    client._http = http
    client._closed = False

    await client.delete_reaction("1", "2", "😀")

    http.delete_reaction.assert_called_once_with("1", "2", "😀")


@pytest.mark.asyncio
async def test_get_reactions_parses_users():
    users_payload = [{"id": "1", "username": "u", "discriminator": "0001"}]
    http = SimpleNamespace(get_reactions=AsyncMock(return_value=users_payload))
    client = Client.__new__(Client)
    client._http = http
    client._closed = False
    client._users = {}

    users = await client.get_reactions("1", "2", "😀")

    http.get_reactions.assert_called_once_with("1", "2", "😀")
    assert isinstance(users[0], User)
