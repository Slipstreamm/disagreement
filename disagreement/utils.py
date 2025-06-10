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
