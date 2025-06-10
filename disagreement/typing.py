import asyncio
from contextlib import suppress
from typing import Optional, TYPE_CHECKING

from .errors import DisagreementException

if TYPE_CHECKING:
    from .client import Client

if __name__ == "typing":
    # For direct module execution testing
    pass


class Typing:
    """Async context manager for Discord typing indicator."""

    def __init__(self, client: "Client", channel_id: str) -> None:
        self._client = client
        self._channel_id = channel_id
        self._task: Optional[asyncio.Task] = None

    async def _run(self) -> None:
        try:
            while True:
                await self._client._http.trigger_typing(self._channel_id)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass

    async def __aenter__(self) -> "Typing":
        if self._client._closed:
            raise DisagreementException("Client is closed.")
        await self._client._http.trigger_typing(self._channel_id)
        self._task = asyncio.create_task(self._run())
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
