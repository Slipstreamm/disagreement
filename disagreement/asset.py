"""Utility class for Discord CDN assets."""

from __future__ import annotations

import os
from typing import IO, Optional, Union, TYPE_CHECKING

import aiohttp  # pylint: disable=import-error

if TYPE_CHECKING:
    from .client import Client


class Asset:
    """Represents a CDN asset such as an avatar or icon."""

    def __init__(self, url: str, client_instance: Optional["Client"] = None) -> None:
        self.url = url
        self._client = client_instance

    async def read(self) -> bytes:
        """Read the asset's bytes."""

        session: Optional[aiohttp.ClientSession] = None
        if self._client is not None:
            await self._client._http._ensure_session()  # type: ignore[attr-defined]
            session = self._client._http._session  # type: ignore[attr-defined]
        if session is None:
            session = aiohttp.ClientSession()
            close = True
        else:
            close = False
        async with session.get(self.url) as resp:
            data = await resp.read()
        if close:
            await session.close()
        return data

    async def save(self, fp: Union[str, os.PathLike[str], IO[bytes]]) -> None:
        """Save the asset to the given file path or file-like object."""

        data = await self.read()
        if isinstance(fp, (str, os.PathLike)):
            path = os.fspath(fp)
            with open(path, "wb") as file:
                file.write(data)
        else:
            fp.write(data)

    def __repr__(self) -> str:
        return f"<Asset url='{self.url}'>"
