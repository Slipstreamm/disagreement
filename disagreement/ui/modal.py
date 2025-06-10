from __future__ import annotations

from typing import Any, Callable, Coroutine, Optional, List, TYPE_CHECKING
import asyncio

from .item import Item
from .view import View
from ..enums import ComponentType, TextInputStyle
from ..models import ActionRow

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from ..interactions import Interaction


class TextInput(Item):
    """Represents a text input component inside a modal."""

    def __init__(
        self,
        *,
        label: str,
        custom_id: Optional[str] = None,
        style: TextInputStyle = TextInputStyle.SHORT,
        placeholder: Optional[str] = None,
        required: bool = True,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        row: Optional[int] = None,
    ) -> None:
        super().__init__(type=ComponentType.TEXT_INPUT)
        self.label = label
        self.custom_id = custom_id
        self.style = style
        self.placeholder = placeholder
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
        self._row = row

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "type": ComponentType.TEXT_INPUT.value,
            "style": self.style.value,
            "label": self.label,
            "required": self.required,
        }
        if self.custom_id:
            payload["custom_id"] = self.custom_id
        if self.placeholder:
            payload["placeholder"] = self.placeholder
        if self.min_length is not None:
            payload["min_length"] = self.min_length
        if self.max_length is not None:
            payload["max_length"] = self.max_length
        return payload


def text_input(
    *,
    label: str,
    custom_id: Optional[str] = None,
    style: TextInputStyle = TextInputStyle.SHORT,
    placeholder: Optional[str] = None,
    required: bool = True,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    row: Optional[int] = None,
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], TextInput]:
    """Decorator to define a text input callback inside a :class:`Modal`."""

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> TextInput:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("TextInput callback must be a coroutine function.")

        item = TextInput(
            label=label,
            custom_id=custom_id or func.__name__,
            style=style,
            placeholder=placeholder,
            required=required,
            min_length=min_length,
            max_length=max_length,
            row=row,
        )
        item.callback = func
        return item

    return decorator


class Modal:
    """Represents a modal dialog."""

    def __init__(self, *, title: str, custom_id: str) -> None:
        self.title = title
        self.custom_id = custom_id
        self._children: List[TextInput] = []

        for item in self.__class__.__dict__.values():
            if isinstance(item, TextInput):
                self.add_item(item)

    @property
    def children(self) -> List[TextInput]:
        return self._children

    def add_item(self, item: TextInput) -> None:
        if not isinstance(item, TextInput):
            raise TypeError("Only TextInput items can be added to a Modal.")
        if len(self._children) >= 5:
            raise ValueError("A modal can only have up to 5 text inputs.")
        item._view = None  # Not part of a view but reuse item base
        self._children.append(item)

    def to_components(self) -> List[ActionRow]:
        rows: List[ActionRow] = []
        for child in self.children:
            row = ActionRow(components=[child])
            rows.append(row)
        return rows

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "custom_id": self.custom_id,
            "components": [r.to_dict() for r in self.to_components()],
        }

    async def callback(
        self, interaction: Interaction
    ) -> None:  # pragma: no cover - default
        pass
