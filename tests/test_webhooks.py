import pytest
from unittest.mock import AsyncMock

from disagreement.http import HTTPClient


@pytest.mark.asyncio
async def test_create_followup_message_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock()
    payload = {"content": "hello"}
    await http.create_followup_message("app_id", "token", payload)
    http.request.assert_called_once_with(
        "POST",
        f"/webhooks/app_id/token",
        payload=payload,
        use_auth_header=False,
    )


@pytest.mark.asyncio
async def test_edit_followup_message_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock()
    payload = {"content": "new content"}
    await http.edit_followup_message("app_id", "token", "123", payload)
    http.request.assert_called_once_with(
        "PATCH",
        f"/webhooks/app_id/token/messages/123",
        payload=payload,
        use_auth_header=False,
    )


@pytest.mark.asyncio
async def test_delete_followup_message_calls_request():
    http = HTTPClient(token="t")
    http.request = AsyncMock()
    await http.delete_followup_message("app_id", "token", "456")
    http.request.assert_called_once_with(
        "DELETE",
        f"/webhooks/app_id/token/messages/456",
        use_auth_header=False,
    )
