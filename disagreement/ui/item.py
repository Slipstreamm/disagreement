from __future__ import annotations

from typing import Any, Callable, Coroutine, Optional, TYPE_CHECKING

from ..models import Component

if TYPE_CHECKING:
    from .view import View
    from ..interactions import Interaction


class Item(Component):
    """Represents a UI item that can be placed in a View.

    This is a base class and is not meant to be used directly.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._view: Optional[View] = None
        self._row: Optional[int] = None
        # This is the callback associated with this item.
        self.callback: Optional[
            Callable[["View", Interaction], Coroutine[Any, Any, Any]]
        ] = None

    @property
    def view(self) -> Optional[View]:
        return self._view

    @property
    def row(self) -> Optional[int]:
        return self._row

    def _refresh_from_data(self, data: dict[str, Any]) -> None:
        # This is used to update the item's state from incoming interaction data.
        # For example, a button's disabled state could be updated here.
        pass
