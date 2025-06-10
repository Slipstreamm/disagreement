# disagreement/event_dispatcher.py

"""
Event dispatcher for handling Discord Gateway events.
"""

import asyncio
import inspect
from collections import defaultdict
from typing import (
    Callable,
    Coroutine,
    Any,
    Dict,
    List,
    Set,
    TYPE_CHECKING,
    Awaitable,
    Optional,
)

from .models import Message, User  # Assuming User might be part of other events
from .errors import DisagreementException

if TYPE_CHECKING:
    from .client import Client  # For type hinting to avoid circular imports
    from .interactions import Interaction

# Type alias for an event listener
EventListener = Callable[..., Awaitable[None]]


class EventDispatcher:
    """
    Manages registration and dispatching of event listeners.
    """

    def __init__(self, client_instance: "Client"):
        self._client: "Client" = client_instance
        self._listeners: Dict[str, List[EventListener]] = defaultdict(list)
        self._waiters: Dict[
            str, List[tuple[asyncio.Future, Optional[Callable[[Any], bool]]]]
        ] = defaultdict(list)
        self.on_dispatch_error: Optional[
            Callable[[str, Exception, EventListener], Awaitable[None]]
        ] = None
        # Pre-defined parsers for specific event types to convert raw data to models
        self._event_parsers: Dict[str, Callable[[Dict[str, Any]], Any]] = {
            "MESSAGE_CREATE": self._parse_message_create,
            "MESSAGE_UPDATE": self._parse_message_update,
            "MESSAGE_DELETE": self._parse_message_delete,
            "MESSAGE_REACTION_ADD": self._parse_message_reaction,
            "MESSAGE_REACTION_REMOVE": self._parse_message_reaction,
            "INTERACTION_CREATE": self._parse_interaction_create,
            "GUILD_CREATE": self._parse_guild_create,
            "CHANNEL_CREATE": self._parse_channel_create,
            "CHANNEL_UPDATE": self._parse_channel_update,
            "PRESENCE_UPDATE": self._parse_presence_update,
            "GUILD_MEMBER_ADD": self._parse_guild_member_add,
            "GUILD_MEMBER_REMOVE": self._parse_guild_member_remove,
            "GUILD_BAN_ADD": self._parse_guild_ban_add,
            "GUILD_BAN_REMOVE": self._parse_guild_ban_remove,
            "GUILD_ROLE_UPDATE": self._parse_guild_role_update,
            "TYPING_START": self._parse_typing_start,
        }

    def _parse_message_create(self, data: Dict[str, Any]) -> Message:
        """Parses raw MESSAGE_CREATE data into a Message object."""
        return self._client.parse_message(data)

    def _parse_message_update(self, data: Dict[str, Any]) -> Message:
        """Parses raw MESSAGE_UPDATE data into a Message object."""
        return self._client.parse_message(data)

    def _parse_message_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parses MESSAGE_DELETE and updates message cache."""
        message_id = data.get("id")
        if message_id:
            self._client._messages.pop(message_id, None)
        return data

    def _parse_message_reaction_raw(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Returns the raw reaction payload."""
        return data

    def _parse_interaction_create(self, data: Dict[str, Any]) -> "Interaction":
        """Parses raw INTERACTION_CREATE data into an Interaction object."""
        from .interactions import Interaction

        return Interaction(data=data, client_instance=self._client)

    def _parse_guild_create(self, data: Dict[str, Any]):
        """Parses raw GUILD_CREATE data into a Guild object."""

        return self._client.parse_guild(data)

    def _parse_channel_create(self, data: Dict[str, Any]):
        """Parses raw CHANNEL_CREATE data into a Channel object."""

        return self._client.parse_channel(data)

    def _parse_presence_update(self, data: Dict[str, Any]):
        """Parses raw PRESENCE_UPDATE data into a PresenceUpdate object."""

        from .models import PresenceUpdate

        return PresenceUpdate(data, client_instance=self._client)

    def _parse_typing_start(self, data: Dict[str, Any]):
        """Parses raw TYPING_START data into a TypingStart object."""

        from .models import TypingStart

        return TypingStart(data, client_instance=self._client)

    def _parse_message_reaction(self, data: Dict[str, Any]):
        """Parses raw reaction data into a Reaction object."""

        from .models import Reaction

        return Reaction(data, client_instance=self._client)

    def _parse_guild_member_add(self, data: Dict[str, Any]):
        """Parses GUILD_MEMBER_ADD into a Member object."""

        guild_id = str(data.get("guild_id"))
        return self._client.parse_member(data, guild_id)

    def _parse_guild_member_remove(self, data: Dict[str, Any]):
        """Parses GUILD_MEMBER_REMOVE into a GuildMemberRemove model."""

        from .models import GuildMemberRemove

        return GuildMemberRemove(data, client_instance=self._client)

    def _parse_guild_ban_add(self, data: Dict[str, Any]):
        """Parses GUILD_BAN_ADD into a GuildBanAdd model."""

        from .models import GuildBanAdd

        return GuildBanAdd(data, client_instance=self._client)

    def _parse_guild_ban_remove(self, data: Dict[str, Any]):
        """Parses GUILD_BAN_REMOVE into a GuildBanRemove model."""

        from .models import GuildBanRemove

        return GuildBanRemove(data, client_instance=self._client)

    def _parse_channel_update(self, data: Dict[str, Any]):
        """Parses CHANNEL_UPDATE into a Channel object."""

        return self._client.parse_channel(data)

    def _parse_guild_role_update(self, data: Dict[str, Any]):
        """Parses GUILD_ROLE_UPDATE into a GuildRoleUpdate model."""

        from .models import GuildRoleUpdate

        return GuildRoleUpdate(data, client_instance=self._client)

    # Potentially add _parse_user for events that directly provide a full user object
    # def _parse_user_update(self, data: Dict[str, Any]) -> User:
    #     return User(data=data)

    def register(self, event_name: str, coro: EventListener):
        """
        Registers a coroutine function to listen for a specific event.

        Args:
            event_name (str): The name of the event (e.g., 'MESSAGE_CREATE').
            coro (Callable): The coroutine function to call when the event occurs.
                             It should accept arguments appropriate for the event.

        Raises:
            TypeError: If the provided callback is not a coroutine function.
        """
        if not inspect.iscoroutinefunction(coro):
            raise TypeError(
                f"Event listener for '{event_name}' must be a coroutine function (async def)."
            )

        # Normalize event name, e.g., 'on_message' -> 'MESSAGE_CREATE'
        # For now, we assume event_name is already the Discord event type string.
        # If using decorators like @client.on_message, the decorator would handle this mapping.
        self._listeners[event_name.upper()].append(coro)

    def unregister(self, event_name: str, coro: EventListener):
        """
        Unregisters a coroutine function from an event.

        Args:
            event_name (str): The name of the event.
            coro (Callable): The coroutine function to unregister.
        """
        event_name_upper = event_name.upper()
        if event_name_upper in self._listeners:
            try:
                self._listeners[event_name_upper].remove(coro)
            except ValueError:
                pass  # Listener not in list

    def add_waiter(
        self,
        event_name: str,
        future: asyncio.Future,
        check: Optional[Callable[[Any], bool]] = None,
    ) -> None:
        self._waiters[event_name.upper()].append((future, check))

    def remove_waiter(self, event_name: str, future: asyncio.Future) -> None:
        waiters = self._waiters.get(event_name.upper())
        if not waiters:
            return
        self._waiters[event_name.upper()] = [
            (f, c) for f, c in waiters if f is not future
        ]
        if not self._waiters[event_name.upper()]:
            self._waiters.pop(event_name.upper(), None)

    def _resolve_waiters(self, event_name: str, data: Any) -> None:
        waiters = self._waiters.get(event_name)
        if not waiters:
            return
        to_remove: List[tuple[asyncio.Future, Optional[Callable[[Any], bool]]]] = []
        for future, check in waiters:
            if future.cancelled():
                to_remove.append((future, check))
                continue
            try:
                if check is None or check(data):
                    future.set_result(data)
                    to_remove.append((future, check))
            except Exception as exc:
                future.set_exception(exc)
                to_remove.append((future, check))
        for item in to_remove:
            if item in waiters:
                waiters.remove(item)
        if not waiters:
            self._waiters.pop(event_name, None)

    async def _dispatch_to_listeners(self, event_name: str, data: Any) -> None:
        listeners = self._listeners.get(event_name)
        if not listeners:
            return

        self._resolve_waiters(event_name, data)

        for listener in listeners:
            try:
                sig = inspect.signature(listener)
                num_params = len(sig.parameters)

                if num_params == 0:
                    await listener()
                elif num_params == 1:
                    await listener(data)
                else:
                    print(
                        f"Warning: Listener {listener.__name__} for {event_name} has an unhandled number of parameters ({num_params}). Skipping or attempting with one arg."
                    )
                    if num_params > 0:
                        await listener(data)

            except Exception as e:
                callback = self.on_dispatch_error
                if callback is not None:
                    try:
                        await callback(event_name, e, listener)
                    except Exception as hook_error:
                        print(f"Error in on_dispatch_error hook itself: {hook_error}")
                else:
                    print(
                        f"Error in event listener {listener.__name__} for {event_name}: {e}"
                    )
                    if hasattr(self._client, "on_error"):
                        try:
                            await self._client.on_error(event_name, e, listener)
                        except Exception as client_err_e:
                            print(f"Error in client.on_error itself: {client_err_e}")

    async def dispatch(self, event_name: str, raw_data: Dict[str, Any]):
        """Dispatch an event and its raw counterpart to all listeners."""

        event_name_upper = event_name.upper()
        raw_event_name = f"RAW_{event_name_upper}"

        await self._dispatch_to_listeners(raw_event_name, raw_data)

        parsed_data: Any = raw_data
        if event_name_upper in self._event_parsers:
            try:
                parser = self._event_parsers[event_name_upper]
                parsed_data = parser(raw_data)
            except Exception as e:
                print(f"Error parsing event data for {event_name_upper}: {e}")
                return

        await self._dispatch_to_listeners(event_name_upper, parsed_data)
