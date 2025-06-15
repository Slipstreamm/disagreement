"""Utility helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type hinting only
    from .models import Message, TextChannel


def utcnow() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(timezone.utc)


async def message_pager(
    channel: "TextChannel",
    *,
    limit: Optional[int] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
) -> AsyncIterator["Message"]:
    """Asynchronously paginate a channel's messages.

    Parameters
    ----------
    channel:
        The :class:`TextChannel` to fetch messages from.
    limit:
        The maximum number of messages to yield. ``None`` fetches until no
        more messages are returned.
    before:
        Fetch messages with IDs less than this snowflake.
    after:
        Fetch messages with IDs greater than this snowflake.

    Yields
    ------
    Message
        Messages in the channel, oldest first.
    """

    remaining = limit
    last_id = before
    while remaining is None or remaining > 0:
        fetch_limit = 100
        if remaining is not None:
            fetch_limit = min(fetch_limit, remaining)

        params: Dict[str, Any] = {"limit": fetch_limit}
        if last_id is not None:
            params["before"] = last_id
        if after is not None:
            params["after"] = after

        data = await channel._client._http.request(  # type: ignore[attr-defined]
            "GET",
            f"/channels/{channel.id}/messages",
            params=params,
        )

        if not data:
            break

        for raw in data:
            msg = channel._client.parse_message(raw)  # type: ignore[attr-defined]
            yield msg
            last_id = msg.id
            if remaining is not None:
                remaining -= 1
                if remaining == 0:
                    return


class Paginator:
    """Helper to split text into pages under a character limit."""

    def __init__(self, limit: int = 2000) -> None:
        self.limit = limit
        self._pages: list[str] = []
        self._current = ""

    def add_line(self, line: str) -> None:
        """Add a line of text to the paginator."""
        if len(line) > self.limit:
            if self._current:
                self._pages.append(self._current)
                self._current = ""
            for i in range(0, len(line), self.limit):
                chunk = line[i : i + self.limit]
                if len(chunk) == self.limit:
                    self._pages.append(chunk)
                else:
                    self._current = chunk
            return

        if not self._current:
            self._current = line
        elif len(self._current) + 1 + len(line) <= self.limit:
            self._current += "\n" + line
        else:
            self._pages.append(self._current)
            self._current = line

    @property
    def pages(self) -> list[str]:
        """Return the accumulated pages."""
        pages = list(self._pages)
        if self._current:
            pages.append(self._current)
        return pages
