# disagreement/ext/commands/cog.py

import inspect
from typing import TYPE_CHECKING, List, Tuple, Callable, Awaitable, Any, Dict, Union

if TYPE_CHECKING:
    from disagreement.client import Client
    from .core import Command
    from disagreement.ext.app_commands.commands import (
        AppCommand,
        AppCommandGroup,
    )  # Added
else:  # pragma: no cover - runtime imports for isinstance checks
    from disagreement.ext.app_commands.commands import AppCommand, AppCommandGroup

    # EventDispatcher might be needed if cogs register listeners directly
    # from disagreement.event_dispatcher import EventDispatcher


class Cog:
    """
    The base class for cogs, which are collections of commands and listeners.
    """

    def __init__(self, client: "Client"):
        self._client: "Client" = client
        self._cog_name: str = self.__class__.__name__
        self._commands: Dict[str, "Command"] = {}
        self._listeners: List[Tuple[str, Callable[..., Awaitable[None]]]] = []
        self._app_commands_and_groups: List[Union["AppCommand", "AppCommandGroup"]] = (
            []
        )  # Added

        # Discover commands and listeners defined in this cog instance
        self._inject()

    @property
    def client(self) -> "Client":
        return self._client

    @property
    def cog_name(self) -> str:
        return self._cog_name

    def _inject(self) -> None:
        """
        Called to discover and prepare commands and listeners within this cog.
        This is typically called by the CommandHandler when adding the cog.
        """
        # Clear any previously injected state (e.g., if re-injecting)
        self._commands.clear()
        self._listeners.clear()
        self._app_commands_and_groups.clear()  # Added

        for member_name, member in inspect.getmembers(self):
            if hasattr(member, "__command_object__"):
                # This is a prefix or hybrid command object
                cmd: "Command" = getattr(member, "__command_object__")
                cmd.cog = self  # Assign the cog instance to the command
                if cmd.name in self._commands:
                    # This should ideally be caught earlier or handled by CommandHandler
                    print(
                        f"Warning: Duplicate command name '{cmd.name}' in cog '{self.cog_name}'. Overwriting."
                    )
                self._commands[cmd.name.lower()] = cmd
                # Also register aliases
                for alias in cmd.aliases:
                    self._commands[alias.lower()] = cmd

                # If this command is also an application command (HybridCommand)
                if isinstance(cmd, (AppCommand, AppCommandGroup)):
                    self._app_commands_and_groups.append(cmd)

            elif hasattr(member, "__app_command_object__"):  # Added for app commands
                app_cmd_obj = getattr(member, "__app_command_object__")
                if isinstance(app_cmd_obj, (AppCommand, AppCommandGroup)):
                    if isinstance(app_cmd_obj, AppCommand):
                        app_cmd_obj.cog = self  # Associate cog
                    # For AppCommandGroup, its commands will have cog set individually if they are AppCommands
                    self._app_commands_and_groups.append(app_cmd_obj)
                else:
                    print(
                        f"Warning: Member '{member_name}' in cog '{self.cog_name}' has '__app_command_object__' but it's not an AppCommand or AppCommandGroup."
                    )

            elif isinstance(member, (AppCommand, AppCommandGroup)):
                if isinstance(member, AppCommand):
                    member.cog = self
                self._app_commands_and_groups.append(member)

            elif hasattr(member, "__listener_name__"):
                # This is a method decorated with @commands.Cog.listener or @commands.listener
                if not inspect.iscoroutinefunction(member):
                    # Decorator should have caught this, but double check
                    print(
                        f"Warning: Listener '{member_name}' in cog '{self.cog_name}' is not a coroutine. Skipping."
                    )
                    continue

                event_name: str = getattr(member, "__listener_name__")
                # The callback needs to be the bound method from this cog instance
                self._listeners.append((event_name, member))

    def _eject(self) -> None:
        """
        Called when the cog is being removed.
        The CommandHandler will handle unregistering commands/listeners.
        This method is for any cog-specific cleanup before that.
        """
        # For now, just clear local collections. Actual unregistration is external.
        self._commands.clear()
        self._listeners.clear()
        self._app_commands_and_groups.clear()  # Added

    def get_commands(self) -> List["Command"]:
        """Returns a list of commands in this cog."""
        # Avoid duplicates if aliases point to the same command object
        return list(dict.fromkeys(self._commands.values()))

    def get_listeners(self) -> List[Tuple[str, Callable[..., Awaitable[None]]]]:
        """Returns a list of (event_name, callback) tuples for listeners in this cog."""
        return self._listeners

    def get_app_commands_and_groups(
        self,
    ) -> List[Union["AppCommand", "AppCommandGroup"]]:
        """Returns a list of application commands and groups in this cog."""
        return self._app_commands_and_groups

    async def cog_load(self) -> None:
        """
        A special method that is called when the cog is loaded.
        This is a good place for any asynchronous setup.
        Subclasses should override this if they need async setup.
        """
        pass

    async def cog_unload(self) -> None:
        """
        A special method that is called when the cog is unloaded.
        This is a good place for any asynchronous cleanup.
        Subclasses should override this if they need async cleanup.
        """
        pass

    # Example of how a listener might be defined within a Cog using the decorator
    # from .decorators import listener # Would be imported at module level
    #
    # @listener(name="ON_MESSAGE_CREATE_CUSTOM") # Explicit name
    # async def on_my_event(self, message: 'Message'):
    #     print(f"Cog '{self.cog_name}' received event with message: {message.content}")
    #
    # @listener() # Name derived from method: on_ready
    # async def on_ready(self):
    #     print(f"Cog '{self.cog_name}' is ready.")
