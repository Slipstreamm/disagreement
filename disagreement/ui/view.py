from __future__ import annotations

import asyncio
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional, TYPE_CHECKING

from ..models import ActionRow
from .item import Item

if TYPE_CHECKING:
    from ..client import Client
    from ..interactions import Interaction


class View:
    """Represents a container for UI components that can be sent with a message.

    Args:
        timeout (Optional[float]): The number of seconds to wait for an interaction before the view times out.
                                   Defaults to 180.
    """

    def __init__(self, *, timeout: Optional[float] = 180.0):
        self.timeout = timeout
        self.id = str(uuid.uuid4())
        self.__children: List[Item] = []
        self.__stopped = asyncio.Event()
        self._client: Optional[Client] = None
        self._message_id: Optional[str] = None

        for item in self.__class__.__dict__.values():
            if isinstance(item, Item):
                self.add_item(item)

    @property
    def children(self) -> List[Item]:
        return self.__children

    def add_item(self, item: Item):
        """Adds an item to the view."""
        if not isinstance(item, Item):
            raise TypeError("Only instances of 'Item' can be added to a View.")

        if len(self.__children) >= 25:
            raise ValueError("A view can only have a maximum of 25 components.")

        item._view = self
        self.__children.append(item)

    @property
    def message_id(self) -> Optional[str]:
        return self._message_id

    @message_id.setter
    def message_id(self, value: str):
        self._message_id = value

    def to_components(self) -> List[ActionRow]:
        """Converts the view's children into a list of ActionRow components.

        This retains the original, simple layout behaviour where each item is
        placed in its own :class:`ActionRow` to ensure backward compatibility.
        """

        rows: List[ActionRow] = []

        for item in self.children:
            if item.custom_id is None:
                item.custom_id = (
                    f"{self.id}:{item.__class__.__name__}:{len(self.__children)}"
                )

            rows.append(ActionRow(components=[item]))

        return rows

    def layout_components_advanced(self) -> List[ActionRow]:
        """Group compatible components into rows following Discord rules."""

        rows: List[ActionRow] = []

        for item in self.children:
            if item.custom_id is None:
                item.custom_id = (
                    f"{self.id}:{item.__class__.__name__}:{len(self.__children)}"
                )

            target_row = item.row
            if target_row is not None:
                if not 0 <= target_row <= 4:
                    raise ValueError("Row index must be between 0 and 4.")

                while len(rows) <= target_row:
                    if len(rows) >= 5:
                        raise ValueError("A view can have at most 5 action rows.")
                    rows.append(ActionRow())

                rows[target_row].add_component(item)
                continue

            placed = False
            for row in rows:
                try:
                    row.add_component(item)
                    placed = True
                    break
                except ValueError:
                    continue

            if not placed:
                if len(rows) >= 5:
                    raise ValueError("A view can have at most 5 action rows.")
                new_row = ActionRow([item])
                rows.append(new_row)

        return rows

    def to_components_payload(self) -> List[Dict[str, Any]]:
        """Converts the view's children into a list of component dictionaries
        that can be sent to the Discord API."""
        return [row.to_dict() for row in self.to_components()]

    async def _dispatch(self, interaction: Interaction):
        """Called by the client to dispatch an interaction to the correct item."""
        if self.timeout is not None:
            self.__stopped.set()  # Reset the timeout on each interaction
            self.__stopped.clear()

        if interaction.data:
            custom_id = interaction.data.custom_id
            for child in self.children:
                if child.custom_id == custom_id:
                    if child.callback:
                        await child.callback(self, interaction)
                    break

    async def wait(self) -> bool:
        """Waits until the view has stopped interacting."""
        return await self.__stopped.wait()

    def stop(self):
        """Stops the view from listening to interactions."""
        if not self.__stopped.is_set():
            self.__stopped.set()

    async def on_timeout(self):
        """Called when the view times out."""
        pass  # User can override this

    async def _start(self, client: Client):
        """Starts the view's internal listener."""
        self._client = client
        if self.timeout is not None:
            asyncio.create_task(self._timeout_task())

    async def _timeout_task(self):
        """The task that waits for the timeout and then stops the view."""
        try:
            await asyncio.wait_for(self.wait(), timeout=self.timeout)
        except asyncio.TimeoutError:
            self.stop()
            await self.on_timeout()
            if self._client and self._message_id:
                # Remove the view from the client's listeners
                self._client._views.pop(self._message_id, None)
