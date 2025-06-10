# OAuth2 Setup

This guide explains how to perform a basic OAuth2 flow with `disagreement`.

1. Generate the authorization URL:

```python
from disagreement.oauth import build_authorization_url

url = build_authorization_url(
    client_id="YOUR_CLIENT_ID",
    redirect_uri="https://your.app/callback",
    scope=["identify"],
)
print(url)
```

2. After the user authorizes your application and you receive a code, exchange it for a token:

```python
import aiohttp
from disagreement.oauth import exchange_code_for_token

async def get_token(code: str):
    return await exchange_code_for_token(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        code=code,
        redirect_uri="https://your.app/callback",
    )
```

`exchange_code_for_token` returns the JSON payload from Discord which includes
`access_token`, `refresh_token` and expiry information.

3. When the access token expires, you can refresh it using the provided refresh
token:

```python
from disagreement.oauth import refresh_access_token

async def refresh(token: str):
    return await refresh_access_token(
        refresh_token=token,
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
    )
```
