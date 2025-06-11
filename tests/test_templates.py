import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.http import HTTPClient
from disagreement.client import Client
from disagreement.models import GuildTemplate


@pytest.mark.asyncio
async def test_get_guild_templates_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value=[])
    await http.get_guild_templates("1")
    http.request.assert_called_once_with("GET", "/guilds/1/templates")


@pytest.mark.asyncio
async def test_client_fetch_templates_returns_models():
    http = SimpleNamespace(
        get_guild_templates=AsyncMock(
            return_value=[
                {
                    "code": "c",
                    "name": "n",
                    "usage_count": 0,
                    "creator_id": "u",
                    "created_at": "t",
                    "updated_at": "t",
                    "source_guild_id": "g",
                }
            ]
        )
    )
    client = Client.__new__(Client)
    client._http = http
    client._closed = False

    templates = await client.fetch_templates("g")

    http.get_guild_templates.assert_awaited_once_with("g")
    assert isinstance(templates[0], GuildTemplate)
