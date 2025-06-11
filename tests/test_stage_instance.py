import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.http import HTTPClient
from disagreement.models import StageChannel, StageInstance
from disagreement.enums import ChannelType


@pytest.mark.asyncio
async def test_http_start_stage_instance_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={"id": "1", "channel_id": "c", "topic": "t"})
    payload = {"channel_id": "c", "topic": "t", "privacy_level": 2}
    instance = await http.start_stage_instance(payload)
    http.request.assert_called_once_with(
        "POST",
        "/stage-instances",
        payload=payload,
        custom_headers=None,
    )
    assert isinstance(instance, StageInstance)


@pytest.mark.asyncio
async def test_http_end_stage_instance_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value=None)
    await http.end_stage_instance("c")
    http.request.assert_called_once_with(
        "DELETE", "/stage-instances/c", custom_headers=None
    )


@pytest.mark.asyncio
async def test_stage_channel_start_and_end():
    http = SimpleNamespace(
        start_stage_instance=AsyncMock(
            return_value=StageInstance({"id": "1", "channel_id": "c", "topic": "hi"})
        ),
        edit_stage_instance=AsyncMock(
            return_value=StageInstance({"id": "1", "channel_id": "c", "topic": "hi"})
        ),
        end_stage_instance=AsyncMock(),
    )
    client = type("Client", (), {})()
    client._http = http
    channel_data = {
        "id": "c",
        "type": ChannelType.GUILD_STAGE_VOICE.value,
        "guild_id": "g",
    }
    channel = StageChannel(channel_data, client)

    instance = await channel.start_stage_instance("hi")
    http.start_stage_instance.assert_awaited_once_with(
        {"channel_id": "c", "topic": "hi", "privacy_level": 2}, reason=None
    )
    assert isinstance(instance, StageInstance)
    assert instance._client is client

    await channel.end_stage_instance()
    http.end_stage_instance.assert_awaited_once_with("c", reason=None)
