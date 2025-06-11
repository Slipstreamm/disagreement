import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from disagreement.http import HTTPClient


class DummyResp:
    def __init__(self, status, headers=None, data=None):
        self.status = status
        self.headers = headers or {}
        self._data = data or {}
        self.headers.setdefault("Content-Type", "application/json")

    async def json(self):
        return self._data

    async def text(self):
        return str(self._data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_request_acquires_and_releases(monkeypatch):
    http = HTTPClient(token="t")
    monkeypatch.setattr(http, "_ensure_session", AsyncMock())
    resp = DummyResp(200)
    http._session = SimpleNamespace(request=MagicMock(return_value=resp))
    http._rate_limiter.acquire = AsyncMock()
    http._rate_limiter.release = MagicMock()
    http._rate_limiter.handle_rate_limit = AsyncMock()

    await http.request("GET", "/a")

    http._rate_limiter.acquire.assert_awaited_once_with("GET:/a")
    http._rate_limiter.release.assert_called_once_with("GET:/a", resp.headers)
    http._rate_limiter.handle_rate_limit.assert_not_called()


@pytest.mark.asyncio
async def test_request_handles_rate_limit(monkeypatch):
    http = HTTPClient(token="t")
    monkeypatch.setattr(http, "_ensure_session", AsyncMock())
    resp1 = DummyResp(
        429,
        {
            "Retry-After": "0.1",
            "X-RateLimit-Global": "false",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset-After": "0.1",
        },
        {"message": "slow"},
    )
    resp2 = DummyResp(200, {}, {})
    http._session = SimpleNamespace(request=MagicMock(side_effect=[resp1, resp2]))
    http._rate_limiter.acquire = AsyncMock()
    http._rate_limiter.release = MagicMock()
    http._rate_limiter.handle_rate_limit = AsyncMock()

    result = await http.request("GET", "/a")

    assert http._rate_limiter.acquire.await_count == 2
    assert http._rate_limiter.release.call_count == 2
    http._rate_limiter.handle_rate_limit.assert_awaited_once_with("GET:/a", 0.1, False)
    assert result == {}
