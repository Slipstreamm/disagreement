import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from disagreement.client import Client
from disagreement.http import HTTPClient
from disagreement.models import TextChannel, Invite


@pytest.mark.asyncio
async def test_create_channel_invite_calls_request_and_returns_model():
    http = HTTPClient(token="t")
    http.request = AsyncMock(return_value={"code": "abc"})
    invite = await http.create_channel_invite("123", {"max_age": 60}, reason="r")

    http.request.assert_called_once_with(
        "POST",
        "/channels/123/invites",
        payload={"max_age": 60},
        custom_headers={"X-Audit-Log-Reason": "r"},
    )
    assert isinstance(invite, Invite)


@pytest.mark.asyncio
async def test_textchannel_create_invite_uses_http():
    http = SimpleNamespace(
        create_channel_invite=AsyncMock(return_value=Invite.from_dict({"code": "a"}))
    )
    client = Client(token="t")
    client._http = http

    channel = TextChannel({"id": "c", "type": 0}, client)
    invite = await channel.create_invite(max_age=30, reason="why")

    http.create_channel_invite.assert_awaited_once_with(
        "c", {"max_age": 30}, reason="why"
    )
    assert isinstance(invite, Invite)
