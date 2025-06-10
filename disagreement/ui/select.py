from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, List, Optional, TYPE_CHECKING

from .item import Item
from ..enums import ComponentType
from ..models import SelectOption

if TYPE_CHECKING:
    from ..interactions import Interaction


class Select(Item):
    """Represents a select menu component in a View.

    Args:
        custom_id (str): The developer-defined identifier for the select menu.
        options (List[SelectOption]): The choices in the select menu.
        placeholder (Optional[str]): The placeholder text that is shown if nothing is selected.
        min_values (int): The minimum number of items that must be chosen.
        max_values (int): The maximum number of items that can be chosen.
        disabled (bool): Whether the select menu is disabled.
        row (Optional[int]): The row the select menu should be placed in, from 0 to 4.
    """

    def __init__(
        self,
        *,
        custom_id: str,
        options: List[SelectOption],
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None,
    ):
        super().__init__(type=ComponentType.STRING_SELECT)
        self.custom_id = custom_id
        self.options = options
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled
        self._row = row

    def to_dict(self) -> dict[str, Any]:
        """Converts the select menu to a dictionary that can be sent to Discord."""
        payload = {
            "type": ComponentType.STRING_SELECT.value,
            "custom_id": self.custom_id,
            "options": [option.to_dict() for option in self.options],
            "disabled": self.disabled,
        }
        if self.placeholder:
            payload["placeholder"] = self.placeholder
        if self.min_values is not None:
            payload["min_values"] = self.min_values
        if self.max_values is not None:
            payload["max_values"] = self.max_values
        return payload


def select(
    *,
    custom_id: str,
    options: List[SelectOption],
    placeholder: Optional[str] = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: Optional[int] = None,
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Select]:
    """A decorator to create a select menu in a View."""

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Select:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Select callback must be a coroutine function.")

        item = Select(
            custom_id=custom_id,
            options=options,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        item.callback = func
        return item

    return decorator
