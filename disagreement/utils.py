"""Utility helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, Iterable, Optional, TYPE_CHECKING, Callable
import re

# Discord epoch in milliseconds (2015-01-01T00:00:00Z)
DISCORD_EPOCH = 1420070400000

if TYPE_CHECKING:  # pragma: no cover - for type hinting only
    from .models import Message, TextChannel


def utcnow() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(timezone.utc)


def find(predicate: Callable[[Any], bool], iterable: Iterable[Any]) -> Optional[Any]:
    """Return the first element in ``iterable`` matching the ``predicate``."""
    for element in iterable:
        if predicate(element):
            return element
    return None


def get(iterable: Iterable[Any], **attrs: Any) -> Optional[Any]:
    """Return the first element with matching attributes."""
    def predicate(elem: Any) -> bool:
        return all(getattr(elem, attr, None) == value for attr, value in attrs.items())
    return find(predicate, iterable)


def snowflake_time(snowflake: int) -> datetime:
    """Return the creation time of a Discord snowflake."""
    timestamp_ms = (snowflake >> 22) + DISCORD_EPOCH
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)


async def message_pager(
    channel: "TextChannel",
    *,
    limit: Optional[int] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
) -> AsyncIterator["Message"]:
    """Asynchronously paginate a channel's messages."""
    remaining = limit
    last_id = before
    while remaining is None or remaining > 0:
        fetch_limit = min(100, remaining) if remaining is not None else 100

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


def escape_markdown(text: str) -> str:
    """Escape Discord markdown formatting in ``text``."""
    return re.sub(r"([\\*_~`>|])", r"\\\1", text)


def escape_mentions(text: str) -> str:
    """Escape Discord mentions in ``text``."""
    return text.replace("@", "@\u200b")
