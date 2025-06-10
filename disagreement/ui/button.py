from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, Optional, TYPE_CHECKING

from .item import Item
from ..enums import ComponentType, ButtonStyle
from ..models import PartialEmoji, to_partial_emoji

if TYPE_CHECKING:
    from ..interactions import Interaction


class Button(Item):
    """Represents a button component in a View.

    Args:
        style (ButtonStyle): The style of the button.
        label (Optional[str]): The text that appears on the button.
        emoji (Optional[str | PartialEmoji]): The emoji that appears on the button.
        custom_id (Optional[str]): The developer-defined identifier for the button.
        url (Optional[str]): The URL for the button.
        disabled (bool): Whether the button is disabled.
        row (Optional[int]): The row the button should be placed in, from 0 to 4.
    """

    def __init__(
        self,
        *,
        style: ButtonStyle = ButtonStyle.SECONDARY,
        label: Optional[str] = None,
        emoji: Optional[str | PartialEmoji] = None,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        disabled: bool = False,
        row: Optional[int] = None,
    ):
        super().__init__(type=ComponentType.BUTTON)
        if not label and not emoji:
            raise ValueError("A button must have a label and/or an emoji.")

        if url and custom_id:
            raise ValueError("A button cannot have both a URL and a custom_id.")

        self.style = style
        self.label = label
        self.emoji = to_partial_emoji(emoji)
        self.custom_id = custom_id
        self.url = url
        self.disabled = disabled
        self._row = row

    def to_dict(self) -> dict[str, Any]:
        """Converts the button to a dictionary that can be sent to Discord."""
        payload = {
            "type": ComponentType.BUTTON.value,
            "style": self.style.value,
            "disabled": self.disabled,
        }
        if self.label:
            payload["label"] = self.label
        if self.emoji:
            payload["emoji"] = self.emoji.to_dict()
        if self.url:
            payload["url"] = self.url
        if self.custom_id:
            payload["custom_id"] = self.custom_id
        return payload


def button(
    *,
    label: Optional[str] = None,
    custom_id: Optional[str] = None,
    style: ButtonStyle = ButtonStyle.SECONDARY,
    emoji: Optional[str | PartialEmoji] = None,
    url: Optional[str] = None,
    disabled: bool = False,
    row: Optional[int] = None,
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Button]:
    """A decorator to create a button in a View."""

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Button:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Button callback must be a coroutine function.")

        item = Button(
            label=label,
            custom_id=custom_id,
            style=style,
            emoji=emoji,
            url=url,
            disabled=disabled,
            row=row,
        )
        item.callback = func
        return item

    return decorator
