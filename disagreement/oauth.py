"""OAuth2 utilities."""

from __future__ import annotations

import aiohttp
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urlencode

from .errors import HTTPException


def build_authorization_url(
    client_id: str,
    redirect_uri: str,
    scope: Union[str, List[str]],
    *,
    state: Optional[str] = None,
    response_type: str = "code",
    prompt: Optional[str] = None,
) -> str:
    """Return the Discord OAuth2 authorization URL."""
    if isinstance(scope, list):
        scope = " ".join(scope)

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": response_type,
        "scope": scope,
    }
    if state is not None:
        params["state"] = state
    if prompt is not None:
        params["prompt"] = prompt

    return "https://discord.com/oauth2/authorize?" + urlencode(params)


async def exchange_code_for_token(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    *,
    session: Optional[aiohttp.ClientSession] = None,
) -> Dict[str, Any]:
    """Exchange an authorization code for an access token."""
    close = False
    if session is None:
        session = aiohttp.ClientSession()
        close = True

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    resp = await session.post(
        "https://discord.com/api/v10/oauth2/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        json_data = await resp.json()
        if resp.status != 200:
            raise HTTPException(resp, message="OAuth token exchange failed")
    finally:
        if close:
            await session.close()
    return json_data


async def refresh_access_token(
    refresh_token: str,
    client_id: str,
    client_secret: str,
    *,
    session: Optional[aiohttp.ClientSession] = None,
) -> Dict[str, Any]:
    """Refresh an access token using a refresh token."""

    close = False
    if session is None:
        session = aiohttp.ClientSession()
        close = True

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    resp = await session.post(
        "https://discord.com/api/v10/oauth2/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        json_data = await resp.json()
        if resp.status != 200:
            raise HTTPException(resp, message="OAuth token refresh failed")
    finally:
        if close:
            await session.close()
    return json_data
