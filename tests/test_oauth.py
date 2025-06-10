import pytest
import aiohttp
from unittest.mock import AsyncMock

from disagreement.http import HTTPClient
from disagreement import oauth


@pytest.mark.asyncio
async def test_build_authorization_url():
    url = oauth.build_authorization_url(
        client_id="123",
        redirect_uri="https://example.com/cb",
        scope=["identify", "guilds"],
        state="xyz",
    )
    assert url.startswith("https://discord.com/oauth2/authorize?")
    assert "client_id=123" in url
    assert "state=xyz" in url
    assert "scope=identify+guilds" in url


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_exchange_code_for_token_makes_correct_request(monkeypatch):
    mock_client_response = AsyncMock()
    mock_client_response.status = 200
    mock_client_response.json = AsyncMock(return_value={"access_token": "a"})
    mock_client_response.__aenter__ = AsyncMock(return_value=mock_client_response)
    mock_client_response.__aexit__ = AsyncMock(return_value=None)

    post_mock = AsyncMock(return_value=mock_client_response)
    monkeypatch.setattr("aiohttp.ClientSession.post", post_mock)

    data = await oauth.exchange_code_for_token(
        client_id="id",
        client_secret="secret",
        code="code",
        redirect_uri="https://cb",
    )

    assert data == {"access_token": "a"}
    post_mock.assert_called_once()
    args, kwargs = post_mock.call_args
    assert args[0] == "https://discord.com/api/v10/oauth2/token"
    assert kwargs["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
    assert kwargs["data"]["grant_type"] == "authorization_code"
    assert kwargs["data"]["client_id"] == "id"


@pytest.mark.asyncio
async def test_exchange_code_for_token_custom_session():
    mock_client_response = AsyncMock()
    mock_client_response.status = 200
    mock_client_response.json = AsyncMock(return_value={"access_token": "x"})
    mock_client_response.__aenter__ = AsyncMock(return_value=mock_client_response)
    mock_client_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_client_response)

    data = await oauth.exchange_code_for_token(
        client_id="c1",
        client_secret="c2",
        code="code",
        redirect_uri="https://cb",
        session=mock_session,
    )
    assert data == {"access_token": "x"}
    mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_access_token_success(monkeypatch):
    mock_client_response = AsyncMock()
    mock_client_response.status = 200
    mock_client_response.json = AsyncMock(return_value={"access_token": "b"})
    mock_client_response.__aenter__ = AsyncMock(return_value=mock_client_response)
    mock_client_response.__aexit__ = AsyncMock(return_value=None)

    post_mock = AsyncMock(return_value=mock_client_response)
    monkeypatch.setattr("aiohttp.ClientSession.post", post_mock)

    data = await oauth.refresh_access_token(
        refresh_token="rt",
        client_id="cid",
        client_secret="sec",
    )

    assert data == {"access_token": "b"}
    post_mock.assert_called_once()
    args, kwargs = post_mock.call_args
    assert args[0] == "https://discord.com/api/v10/oauth2/token"
    assert kwargs["data"]["grant_type"] == "refresh_token"
    assert kwargs["data"]["refresh_token"] == "rt"


@pytest.mark.asyncio
async def test_refresh_access_token_error(monkeypatch):
    mock_client_response = AsyncMock()
    mock_client_response.status = 400
    mock_client_response.json = AsyncMock(return_value={"error": "invalid"})
    mock_client_response.__aenter__ = AsyncMock(return_value=mock_client_response)
    mock_client_response.__aexit__ = AsyncMock(return_value=None)

    post_mock = AsyncMock(return_value=mock_client_response)
    monkeypatch.setattr("aiohttp.ClientSession.post", post_mock)

    with pytest.raises(oauth.HTTPException):
        await oauth.refresh_access_token(
            refresh_token="bad",
            client_id="cid",
            client_secret="sec",
        )
