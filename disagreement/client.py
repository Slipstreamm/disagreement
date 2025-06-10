# disagreement/client.py

"""
The main Client class for interacting with the Discord API.
"""

import asyncio
import signal
from typing import (
    Optional,
    Callable,
    Any,
    TYPE_CHECKING,
    Awaitable,
    Union,
    List,
    Dict,
)
from types import ModuleType

from .http import HTTPClient
from .gateway import GatewayClient
from .shard_manager import ShardManager
from .event_dispatcher import EventDispatcher
from .enums import GatewayIntent, InteractionType, GatewayOpcode
from .errors import DisagreementException, AuthenticationError
from .typing import Typing
from .ext.commands.core import CommandHandler
from .ext.commands.cog import Cog
from .ext.app_commands.handler import AppCommandHandler
from .ext.app_commands.context import AppCommandContext
from .ext import loader as ext_loader
from .interactions import Interaction, Snowflake
from .error_handler import setup_global_error_handler
from .voice_client import VoiceClient

if TYPE_CHECKING:
    from .models import (
        Message,
        Embed,
        ActionRow,
        Guild,
        Channel,
        User,
        Member,
        Role,
        TextChannel,
        VoiceChannel,
        CategoryChannel,
        Thread,
        DMChannel,
        Webhook,
    )
    from .ui.view import View
    from .enums import ChannelType as EnumChannelType
    from .ext.commands.core import CommandContext
    from .ext.commands.errors import CommandError, CommandInvokeError
    from .ext.app_commands.commands import AppCommand, AppCommandGroup


class Client:
    """
    Represents a client connection that connects to Discord.
    This class is used to interact with the Discord WebSocket and API.

    Args:
        token (str): The bot token for authentication.
        intents (Optional[int]): The Gateway Intents to use. Defaults to `GatewayIntent.default()`.
                                 You might need to enable privileged intents in your bot's application page.
        loop (Optional[asyncio.AbstractEventLoop]): The event loop to use for asynchronous operations.
                                                    Defaults to `asyncio.get_event_loop()`.
        command_prefix (Union[str, List[str], Callable[['Client', Message], Union[str, List[str]]]]):
            The prefix(es) for commands. Defaults to '!'.
        verbose (bool): If True, print raw HTTP and Gateway traffic for debugging.
    """

    def __init__(
        self,
        token: str,
        intents: Optional[int] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        command_prefix: Union[
            str, List[str], Callable[["Client", "Message"], Union[str, List[str]]]
        ] = "!",
        application_id: Optional[Union[str, int]] = None,
        verbose: bool = False,
        mention_replies: bool = False,
        shard_count: Optional[int] = None,
        gateway_max_retries: int = 5,
        gateway_max_backoff: float = 60.0,
    ):
        if not token:
            raise ValueError("A bot token must be provided.")

        self.token: str = token
        self.intents: int = intents if intents is not None else GatewayIntent.default()
        self.loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self.application_id: Optional[Snowflake] = (
            str(application_id) if application_id else None
        )
        setup_global_error_handler(self.loop)

        self.verbose: bool = verbose
        self._http: HTTPClient = HTTPClient(token=self.token, verbose=verbose)
        self._event_dispatcher: EventDispatcher = EventDispatcher(client_instance=self)
        self._gateway: Optional[GatewayClient] = (
            None  # Initialized in run() or connect()
        )
        self.shard_count: Optional[int] = shard_count
        self.gateway_max_retries: int = gateway_max_retries
        self.gateway_max_backoff: float = gateway_max_backoff
        self._shard_manager: Optional[ShardManager] = None

        # Initialize CommandHandler
        self.command_handler: CommandHandler = CommandHandler(
            client=self, prefix=command_prefix
        )
        self.app_command_handler: AppCommandHandler = AppCommandHandler(client=self)
        # Register internal listener for processing commands from messages
        self._event_dispatcher.register(
            "MESSAGE_CREATE", self._process_message_for_commands
        )

        self._closed: bool = False
        self._ready_event: asyncio.Event = asyncio.Event()
        self.application_id: Optional[Snowflake] = None  # For Application Commands
        self.user: Optional["User"] = (
            None  # The bot's own user object, populated on READY
        )

        # Initialize AppCommandHandler
        self.app_command_handler: AppCommandHandler = AppCommandHandler(client=self)

        # Internal Caches
        self._guilds: Dict[Snowflake, "Guild"] = {}
        self._channels: Dict[Snowflake, "Channel"] = (
            {}
        )  # Stores all channel types by ID
        self._users: Dict[Snowflake, Any] = (
            {}
        )  # Placeholder for User model cache if needed
        self._messages: Dict[Snowflake, "Message"] = {}
        self._views: Dict[Snowflake, "View"] = {}
        self._voice_clients: Dict[Snowflake, VoiceClient] = {}
        self._webhooks: Dict[Snowflake, "Webhook"] = {}

        # Default whether replies mention the user
        self.mention_replies: bool = mention_replies

        # Basic signal handling for graceful shutdown
        # This might be better handled by the user's application code, but can be a nice default.
        # For more robust handling, consider libraries or more advanced patterns.
        try:
            self.loop.add_signal_handler(
                signal.SIGINT, lambda: self.loop.create_task(self.close())
            )
            self.loop.add_signal_handler(
                signal.SIGTERM, lambda: self.loop.create_task(self.close())
            )
        except NotImplementedError:
            # add_signal_handler is not available on all platforms (e.g., Windows default event loop policy)
            # Users on these platforms would need to handle shutdown differently.
            print(
                "Warning: Signal handlers for SIGINT/SIGTERM could not be added. "
                "Graceful shutdown via signals might not work as expected on this platform."
            )

    async def _initialize_gateway(self):
        """Initializes the GatewayClient if it doesn't exist."""
        if self._gateway is None:
            self._gateway = GatewayClient(
                http_client=self._http,
                event_dispatcher=self._event_dispatcher,
                token=self.token,
                intents=self.intents,
                client_instance=self,
                verbose=self.verbose,
                max_retries=self.gateway_max_retries,
                max_backoff=self.gateway_max_backoff,
            )

    async def _initialize_shard_manager(self) -> None:
        """Initializes the :class:`ShardManager` if not already created."""
        if self._shard_manager is None:
            count = self.shard_count or 1
            self._shard_manager = ShardManager(self, count)

    async def connect(self, reconnect: bool = True) -> None:
        """
        Establishes a connection to Discord. This includes logging in and connecting to the Gateway.
        This method is a coroutine.

        Args:
            reconnect (bool): Whether to automatically attempt to reconnect on disconnect.
                              (Note: Basic reconnect logic is within GatewayClient for now)

        Raises:
            GatewayException: If the connection to the gateway fails.
            AuthenticationError: If the token is invalid.
        """
        if self._closed:
            raise DisagreementException("Client is closed and cannot connect.")
        if self.shard_count and self.shard_count > 1:
            await self._initialize_shard_manager()
            assert self._shard_manager is not None
            await self._shard_manager.start()
            print(
                f"Client connected using {self.shard_count} shards, waiting for READY signal..."
            )
            await self.wait_until_ready()
            print("Client is READY!")
            return

        await self._initialize_gateway()
        assert self._gateway is not None  # Should be initialized by now

        retry_delay = 5  # seconds
        max_retries = 5  # For initial connection attempts by Client.run, Gateway has its own internal retries for some cases.

        for attempt in range(max_retries):
            try:
                await self._gateway.connect()
                # After successful connection, GatewayClient's HELLO handler will trigger IDENTIFY/RESUME
                # and its READY handler will set self._ready_event via dispatcher.
                print("Client connected to Gateway, waiting for READY signal...")
                await self.wait_until_ready()  # Wait for the READY event from Gateway
                print("Client is READY!")
                return  # Successfully connected and ready
            except AuthenticationError:  # Non-recoverable by retry here
                print("Authentication failed. Please check your bot token.")
                await self.close()  # Ensure cleanup
                raise
            except DisagreementException as e:  # Includes GatewayException
                print(f"Failed to connect (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(
                        retry_delay * 2, 60
                    )  # Exponential backoff up to 60s
                else:
                    print("Max connection retries reached. Giving up.")
                    await self.close()  # Ensure cleanup
                    raise
        # Should not be reached if max_retries is > 0
        if max_retries == 0:  # If max_retries was 0, means no retries attempted
            raise DisagreementException("Connection failed with 0 retries allowed.")

    async def run(self) -> None:
        """
        A blocking call that connects the client to Discord and runs until the client is closed.
        This method is a coroutine.
        It handles login, Gateway connection, and keeping the connection alive.
        """
        if self._closed:
            raise DisagreementException("Client is already closed.")

        try:
            await self.connect()
            # The GatewayClient's _receive_loop will keep running.
            # This run method effectively waits until the client is closed or an unhandled error occurs.
            # A more robust implementation might have a main loop here that monitors gateway health.
            # For now, we rely on the gateway's tasks.
            while not self._closed:
                if (
                    self._gateway
                    and self._gateway._receive_task
                    and self._gateway._receive_task.done()
                ):
                    # If receive task ended unexpectedly, try to handle it or re-raise
                    try:
                        exc = self._gateway._receive_task.exception()
                        if exc:
                            print(
                                f"Gateway receive task ended with exception: {exc}. Attempting to reconnect..."
                            )
                            # This is a basic reconnect strategy from the client side.
                            # GatewayClient itself might handle some reconnects.
                            await self.close_gateway(
                                code=1000
                            )  # Close current gateway state
                            await asyncio.sleep(5)  # Wait before reconnecting
                            if (
                                not self._closed
                            ):  # If client wasn't closed by the exception handler
                                await self.connect()
                            else:
                                break  # Client was closed, exit run loop
                        else:
                            print(
                                "Gateway receive task ended without exception. Assuming clean shutdown or reconnect handled internally."
                            )
                            if (
                                not self._closed
                            ):  # If not explicitly closed, might be an issue
                                print(
                                    "Warning: Gateway receive task ended but client not closed. This might indicate an issue."
                                )
                                # Consider a more robust health check or reconnect strategy here.
                                await asyncio.sleep(
                                    1
                                )  # Prevent tight loop if something is wrong
                            else:
                                break  # Client was closed
                    except asyncio.CancelledError:
                        print("Gateway receive task was cancelled.")
                        break  # Exit if cancelled
                    except Exception as e:
                        print(f"Error checking gateway receive task: {e}")
                        break  # Exit on other errors
                await asyncio.sleep(1)  # Main loop check interval
        except DisagreementException as e:
            print(f"Client run loop encountered an error: {e}")
            # Error already logged by connect or other methods
        except asyncio.CancelledError:
            print("Client run loop was cancelled.")
        finally:
            if not self._closed:
                await self.close()

    async def close(self) -> None:
        """
        Closes the connection to Discord. This method is a coroutine.
        """
        if self._closed:
            return

        self._closed = True
        print("Closing client...")

        if self._shard_manager:
            await self._shard_manager.close()
            self._shard_manager = None
        if self._gateway:
            await self._gateway.close()

        if self._http:  # HTTPClient has its own session to close
            await self._http.close()

        self._ready_event.set()  # Ensure any waiters for ready are unblocked
        print("Client closed.")

    async def __aenter__(self) -> "Client":
        """Enter the context manager by connecting to Discord."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc: Optional[BaseException],
        tb: Optional[BaseException],
    ) -> bool:
        """Exit the context manager and close the client."""
        await self.close()
        return False

    async def close_gateway(self, code: int = 1000) -> None:
        """Closes only the gateway connection, allowing for potential reconnect."""
        if self._shard_manager:
            await self._shard_manager.close()
            self._shard_manager = None
        if self._gateway:
            await self._gateway.close(code=code)
            self._gateway = None
        self._ready_event.clear()  # No longer ready if gateway is closed

    def is_closed(self) -> bool:
        """Indicates if the client has been closed."""
        return self._closed

    def is_ready(self) -> bool:
        """Indicates if the client has successfully connected to the Gateway and is ready."""
        return self._ready_event.is_set()

    @property
    def latency(self) -> Optional[float]:
        """Returns the gateway latency in seconds, or ``None`` if unavailable."""
        if self._gateway:
            return self._gateway.latency
        return None

    async def wait_until_ready(self) -> None:
        """|coro|
        Waits until the client is fully connected to Discord and the initial state is processed.
        This is mainly useful for waiting for the READY event from the Gateway.
        """
        await self._ready_event.wait()

    async def wait_for(
        self,
        event_name: str,
        check: Optional[Callable[[Any], bool]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """|coro|
        Waits for a specific event to occur that satisfies the ``check``.

        Parameters
        ----------
        event_name: str
            The name of the event to wait for.
        check: Optional[Callable[[Any], bool]]
            A function that determines whether the received event should resolve the wait.
        timeout: Optional[float]
            How long to wait for the event before raising :class:`asyncio.TimeoutError`.
        """

        future: asyncio.Future = self.loop.create_future()
        self._event_dispatcher.add_waiter(event_name, future, check)
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            self._event_dispatcher.remove_waiter(event_name, future)

    async def change_presence(
        self,
        status: str,
        activity_name: Optional[str] = None,
        activity_type: int = 0,
        since: int = 0,
        afk: bool = False,
    ):
        """
        Changes the client's presence on Discord.

        Args:
            status (str): The new status for the client (e.g., "online", "idle", "dnd", "invisible").
            activity_name (Optional[str]): The name of the activity.
            activity_type (int): The type of the activity.
            since (int): The timestamp (in milliseconds) of when the client went idle.
            afk (bool): Whether the client is AFK.
        """
        if self._closed:
            raise DisagreementException("Client is closed.")

        if self._gateway:
            await self._gateway.update_presence(
                status=status,
                activity_name=activity_name,
                activity_type=activity_type,
                since=since,
                afk=afk,
            )

    # --- Event Handling ---

    def event(
        self, coro: Callable[..., Awaitable[None]]
    ) -> Callable[..., Awaitable[None]]:
        """
        A decorator that registers an event to listen to.
        The name of the coroutine is used as the event name.
        Example:
            @client.event
            async def on_ready(): # Will listen for the 'READY' event
                print("Bot is ready!")

            @client.event
            async def on_message(message: disagreement.Message): # Will listen for 'MESSAGE_CREATE'
                print(f"Message from {message.author}: {message.content}")
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("Event registered must be a coroutine function.")

        event_name = coro.__name__
        # Map common function names to Discord event types
        # e.g., on_ready -> READY, on_message -> MESSAGE_CREATE
        if event_name.startswith("on_"):
            discord_event_name = event_name[3:].upper()
            mapping = {
                "MESSAGE": "MESSAGE_CREATE",
                "MESSAGE_EDIT": "MESSAGE_UPDATE",
                "MESSAGE_UPDATE": "MESSAGE_UPDATE",
                "MESSAGE_DELETE": "MESSAGE_DELETE",
                "REACTION_ADD": "MESSAGE_REACTION_ADD",
                "REACTION_REMOVE": "MESSAGE_REACTION_REMOVE",
            }
            discord_event_name = mapping.get(discord_event_name, discord_event_name)
            self._event_dispatcher.register(discord_event_name, coro)
        else:
            # If not starting with "on_", assume it's the direct Discord event name (e.g. "TYPING_START")
            # Or raise an error if a specific format is required.
            # For now, let's assume direct mapping if no "on_" prefix.
            self._event_dispatcher.register(event_name.upper(), coro)

        return coro  # Return the original coroutine

    def on_event(
        self, event_name: str
    ) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
        """
        A decorator that registers an event to listen to with a specific event name.
        Example:
            @client.on_event('MESSAGE_CREATE')
            async def my_message_handler(message: disagreement.Message):
                print(f"Message: {message.content}")
        """

        def decorator(
            coro: Callable[..., Awaitable[None]],
        ) -> Callable[..., Awaitable[None]]:
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError("Event registered must be a coroutine function.")
            self._event_dispatcher.register(event_name.upper(), coro)
            return coro

        return decorator

    async def _process_message_for_commands(self, message: "Message") -> None:
        """Internal listener to process messages for commands."""
        # Make sure message object is valid and not from a bot (optional, common check)
        if (
            not message or not message.author or message.author.bot
        ):  # Add .bot check to User model
            return
        await self.command_handler.process_commands(message)

    # --- Command Framework Methods ---

    def add_cog(self, cog: Cog) -> None:
        """
        Adds a Cog to the bot.
        Cogs are classes that group commands, listeners, and state.
        This will also discover and register any application commands defined in the cog.

        Args:
            cog (Cog): An instance of a class derived from `disagreement.ext.commands.Cog`.
        """
        # Add to prefix command handler
        self.command_handler.add_cog(
            cog
        )  # This should call cog._inject() internally or cog._inject() is called on Cog init

        # Discover and add application commands from the cog
        # AppCommand and AppCommandGroup are already imported in TYPE_CHECKING block
        for app_cmd_obj in cog.get_app_commands_and_groups():  # Uses the new method
            # The cog attribute should have been set within Cog._inject() for AppCommands
            self.app_command_handler.add_command(app_cmd_obj)
            print(
                f"Registered app command/group '{app_cmd_obj.name}' from cog '{cog.cog_name}'."
            )

    def remove_cog(self, cog_name: str) -> Optional[Cog]:
        """
        Removes a Cog from the bot.

        Args:
            cog_name (str): The name of the Cog to remove.

        Returns:
            Optional[Cog]: The Cog that was removed, or None if not found.
        """
        removed_cog = self.command_handler.remove_cog(cog_name)
        if removed_cog:
            # Also remove associated application commands
            # This requires AppCommand to store a reference to its cog, or iterate all app_commands.
            # Assuming AppCommand has a .cog attribute, which is set in Cog._inject()
            # And AppCommandGroup might store commands that have .cog attribute
            for app_cmd_or_group in removed_cog.get_app_commands_and_groups():
                # The AppCommandHandler.remove_command needs to handle both AppCommand and AppCommandGroup
                self.app_command_handler.remove_command(
                    app_cmd_or_group.name
                )  # Assuming name is unique enough for removal here
                print(
                    f"Removed app command/group '{app_cmd_or_group.name}' from cog '{cog_name}'."
                )
            # Note: AppCommandHandler.remove_command might need to be more specific if names aren't globally unique
            # (e.g. if it needs type or if groups and commands can share names).
            # For now, assuming name is sufficient for removal from the handler's flat list.
        return removed_cog

    def add_app_command(self, command: Union["AppCommand", "AppCommandGroup"]) -> None:
        """
        Adds a standalone application command or group to the bot.
        Use this for commands not defined within a Cog.

        Args:
            command (Union[AppCommand, AppCommandGroup]): The application command or group instance.
                This is typically the object returned by a decorator like @slash_command.
        """
        from .ext.app_commands.commands import (
            AppCommand,
            AppCommandGroup,
        )  # Ensure types

        if not isinstance(command, (AppCommand, AppCommandGroup)):
            raise TypeError(
                "Command must be an instance of AppCommand or AppCommandGroup."
            )

        # If it's a decorated function, the command object might be on __app_command_object__
        if hasattr(command, "__app_command_object__") and isinstance(
            getattr(command, "__app_command_object__"), (AppCommand, AppCommandGroup)
        ):
            actual_command_obj = getattr(command, "__app_command_object__")
            self.app_command_handler.add_command(actual_command_obj)
            print(
                f"Registered standalone app command/group '{actual_command_obj.name}'."
            )
        elif isinstance(
            command, (AppCommand, AppCommandGroup)
        ):  # It's already the command object
            self.app_command_handler.add_command(command)
            print(f"Registered standalone app command/group '{command.name}'.")
        else:
            # This case should ideally not be hit if type checks are done by decorators
            print(
                f"Warning: Could not register app command {command}. It's not a recognized command object or decorated function."
            )

    async def on_command_error(
        self, ctx: "CommandContext", error: "CommandError"
    ) -> None:
        """
        Default command error handler. Called when a command raises an error.
        Users can override this method in a subclass of Client to implement custom error handling.

        Args:
            ctx (CommandContext): The context of the command that raised the error.
            error (CommandError): The error that was raised.
        """
        # Default behavior: print to console.
        # Users might want to send a message to ctx.channel or log to a file.
        print(
            f"Error in command '{ctx.command.name if ctx.command else 'unknown'}': {error}"
        )

        # Need to import CommandInvokeError for this check if not already globally available
        # For now, assuming it's imported via TYPE_CHECKING or directly if needed at runtime
        from .ext.commands.errors import (
            CommandInvokeError as CIE,
        )  # Local import for isinstance check

        if isinstance(error, CIE):
            # Now it's safe to access error.original
            print(
                f"Original exception: {type(error.original).__name__}: {error.original}"
            )
            # import traceback
            # traceback.print_exception(type(error.original), error.original, error.original.__traceback__)

    # --- Extension Management Methods ---

    def load_extension(self, name: str) -> ModuleType:
        """Load an extension by name using :mod:`disagreement.ext.loader`."""

        return ext_loader.load_extension(name)

    def unload_extension(self, name: str) -> None:
        """Unload a previously loaded extension."""

        ext_loader.unload_extension(name)

    def reload_extension(self, name: str) -> ModuleType:
        """Reload an extension by name."""

        return ext_loader.reload_extension(name)

    # --- Model Parsing and Fetching ---

    def parse_user(self, data: Dict[str, Any]) -> "User":
        """Parses user data and returns a User object, updating cache."""
        from .models import User  # Ensure User model is available

        user = User(data)
        self._users[user.id] = user  # Cache the user
        return user

    def parse_channel(self, data: Dict[str, Any]) -> "Channel":
        """Parses channel data and returns a Channel object, updating caches."""

        from .models import channel_factory

        channel = channel_factory(data, self)
        self._channels[channel.id] = channel
        if channel.guild_id:
            guild = self._guilds.get(channel.guild_id)
            if guild:
                guild._channels[channel.id] = channel
        return channel

    def parse_message(self, data: Dict[str, Any]) -> "Message":
        """Parses message data and returns a Message object, updating cache."""

        from .models import Message

        message = Message(data, client_instance=self)
        self._messages[message.id] = message
        return message

    def parse_webhook(self, data: Union[Dict[str, Any], "Webhook"]) -> "Webhook":
        """Parses webhook data and returns a Webhook object, updating cache."""

        from .models import Webhook

        if isinstance(data, Webhook):
            webhook = data
            webhook._client = self  # type: ignore[attr-defined]
        else:
            webhook = Webhook(data, client_instance=self)
        self._webhooks[webhook.id] = webhook
        return webhook

    async def fetch_user(self, user_id: Snowflake) -> Optional["User"]:
        """Fetches a user by ID from Discord."""
        if self._closed:
            raise DisagreementException("Client is closed.")

        cached_user = self._users.get(user_id)
        if cached_user:
            return cached_user  # Return cached if available, though fetch implies wanting fresh

        try:
            user_data = await self._http.get_user(user_id)
            return self.parse_user(user_data)
        except DisagreementException as e:  # Catch HTTP exceptions from http client
            print(f"Failed to fetch user {user_id}: {e}")
            return None

    async def fetch_message(
        self, channel_id: Snowflake, message_id: Snowflake
    ) -> Optional["Message"]:
        """Fetches a message by ID from Discord and caches it."""

        if self._closed:
            raise DisagreementException("Client is closed.")

        cached_message = self._messages.get(message_id)
        if cached_message:
            return cached_message

        try:
            message_data = await self._http.get_message(channel_id, message_id)
            return self.parse_message(message_data)
        except DisagreementException as e:
            print(
                f"Failed to fetch message {message_id} from channel {channel_id}: {e}"
            )
            return None

    def parse_member(self, data: Dict[str, Any], guild_id: Snowflake) -> "Member":
        """Parses member data and returns a Member object, updating relevant caches."""
        from .models import Member  # Ensure Member model is available

        # Member's __init__ should handle the nested 'user' data.
        member = Member(data, client_instance=self)
        member.guild_id = str(guild_id)

        # Cache the member in the guild's member cache
        guild = self._guilds.get(guild_id)
        if guild:
            guild._members[member.id] = member  # Assuming Guild has _members dict

        # Also cache the user part if not already cached or if this is newer
        # Since Member inherits from User, the member object itself is the user.
        self._users[member.id] = member
        # If 'user' was in data and Member.__init__ used it, it's already part of 'member'.
        return member

    async def fetch_member(
        self, guild_id: Snowflake, member_id: Snowflake
    ) -> Optional["Member"]:
        """Fetches a member from a guild by ID."""
        if self._closed:
            raise DisagreementException("Client is closed.")

        guild = self.get_guild(guild_id)
        if guild:
            cached_member = guild.get_member(member_id)  # Use Guild's get_member
            if cached_member:
                return cached_member  # Return cached if available

        try:
            member_data = await self._http.get_guild_member(guild_id, member_id)
            return self.parse_member(member_data, guild_id)
        except DisagreementException as e:
            print(f"Failed to fetch member {member_id} from guild {guild_id}: {e}")
            return None

    def parse_role(self, data: Dict[str, Any], guild_id: Snowflake) -> "Role":
        """Parses role data and returns a Role object, updating guild's role cache."""
        from .models import Role  # Ensure Role model is available

        role = Role(data)
        guild = self._guilds.get(guild_id)
        if guild:
            # Update the role in the guild's roles list if it exists, or add it.
            # Guild.roles is List[Role]. We need to find and replace or append.
            found = False
            for i, existing_role in enumerate(guild.roles):
                if existing_role.id == role.id:
                    guild.roles[i] = role
                    found = True
                    break
            if not found:
                guild.roles.append(role)
        return role

    def parse_guild(self, data: Dict[str, Any]) -> "Guild":
        """Parses guild data and returns a Guild object, updating cache."""

        from .models import Guild

        guild = Guild(data, client_instance=self)
        self._guilds[guild.id] = guild

        # Populate channel and member caches if provided
        for ch in data.get("channels", []):
            channel_obj = self.parse_channel(ch)
            guild._channels[channel_obj.id] = channel_obj

        for member in data.get("members", []):
            member_obj = self.parse_member(member, guild.id)
            guild._members[member_obj.id] = member_obj

        return guild

    async def fetch_roles(self, guild_id: Snowflake) -> List["Role"]:
        """Fetches all roles for a given guild and caches them.

        If the guild is not cached, it will be retrieved first using
        :meth:`fetch_guild`.
        """
        if self._closed:
            raise DisagreementException("Client is closed.")
        guild = self.get_guild(guild_id)
        if not guild:
            guild = await self.fetch_guild(guild_id)
            if not guild:
                return []

        try:
            roles_data = await self._http.get_guild_roles(guild_id)
            parsed_roles = []
            for role_data in roles_data:
                # parse_role will add/update it in the guild.roles list
                parsed_roles.append(self.parse_role(role_data, guild_id))
            guild.roles = parsed_roles  # Replace the entire list with the fresh one
            return parsed_roles
        except DisagreementException as e:
            print(f"Failed to fetch roles for guild {guild_id}: {e}")
            return []

    async def fetch_role(
        self, guild_id: Snowflake, role_id: Snowflake
    ) -> Optional["Role"]:
        """Fetches a specific role from a guild by ID.
        If roles for the guild aren't cached or might be stale, it fetches all roles first.
        """
        guild = self.get_guild(guild_id)
        if guild:
            # Try to find in existing guild.roles
            for role in guild.roles:
                if role.id == role_id:
                    return role

        # If not found in cache or guild doesn't exist yet in cache, fetch all roles for the guild
        await self.fetch_roles(guild_id)  # This will populate/update guild.roles

        # Try again from the now (hopefully) populated cache
        guild = self.get_guild(
            guild_id
        )  # Re-get guild in case it was populated by fetch_roles
        if guild:
            for role in guild.roles:
                if role.id == role_id:
                    return role

        return None  # Role not found even after fetching

    # --- API Methods ---

    # --- API Methods ---

    async def send_message(
        self,
        channel_id: str,
        content: Optional[str] = None,
        *,  # Make additional params keyword-only
        tts: bool = False,
        embed: Optional["Embed"] = None,
        embeds: Optional[List["Embed"]] = None,
        components: Optional[List["ActionRow"]] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
        message_reference: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Any]] = None,
        files: Optional[List[Any]] = None,
        flags: Optional[int] = None,
        view: Optional["View"] = None,
    ) -> "Message":
        """|coro|
        Sends a message to the specified channel.

        Args:
            channel_id (str): The ID of the channel to send the message to.
            content (Optional[str]): The content of the message.
            tts (bool): Whether the message should be sent with text-to-speech. Defaults to False.
            embed (Optional[Embed]): A single embed to send. Cannot be used with `embeds`.
            embeds (Optional[List[Embed]]): A list of embeds to send. Cannot be used with `embed`.
                                            Discord supports up to 10 embeds per message.
            components (Optional[List[ActionRow]]): A list of ActionRow components to include.
            allowed_mentions (Optional[Dict[str, Any]]): Allowed mentions for the message.
            message_reference (Optional[Dict[str, Any]]): Message reference for replying.
            attachments (Optional[List[Any]]): Attachments to include with the message.
            files (Optional[List[Any]]): Files to upload with the message.
            flags (Optional[int]): Message flags.
            view (Optional[View]): A view to send with the message.

        Returns:
            Message: The message that was sent.

        Raises:
            HTTPException: Sending the message failed.
            ValueError: If both `embed` and `embeds` are provided, or if both `components` and `view` are provided.
        """
        if self._closed:
            raise DisagreementException("Client is closed.")

        if embed and embeds:
            raise ValueError("Cannot provide both embed and embeds.")
        if components and view:
            raise ValueError("Cannot provide both 'components' and 'view'.")

        final_embeds_payload: Optional[List[Dict[str, Any]]] = None
        if embed:
            final_embeds_payload = [embed.to_dict()]
        elif embeds:
            from .models import (
                Embed as EmbedModel,
            )

            final_embeds_payload = [
                e.to_dict() for e in embeds if isinstance(e, EmbedModel)
            ]

        components_payload: Optional[List[Dict[str, Any]]] = None
        if view:
            await view._start(self)
            components_payload = view.to_components_payload()
        elif components:
            from .models import Component as ComponentModel

            components_payload = [
                comp.to_dict()
                for comp in components
                if isinstance(comp, ComponentModel)
            ]

        message_data = await self._http.send_message(
            channel_id=channel_id,
            content=content,
            tts=tts,
            embeds=final_embeds_payload,
            components=components_payload,
            allowed_mentions=allowed_mentions,
            message_reference=message_reference,
            attachments=attachments,
            files=files,
            flags=flags,
        )

        if view:
            message_id = message_data["id"]
            view.message_id = message_id
            self._views[message_id] = view

        return self.parse_message(message_data)

    def typing(self, channel_id: str) -> Typing:
        """Return a context manager to show a typing indicator in a channel."""

        return Typing(self, channel_id)

    async def join_voice(
        self,
        guild_id: Snowflake,
        channel_id: Snowflake,
        *,
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> VoiceClient:
        """|coro| Join a voice channel and return a :class:`VoiceClient`."""

        if self._closed:
            raise DisagreementException("Client is closed.")
        if not self.is_ready():
            await self.wait_until_ready()
        if self._gateway is None:
            raise DisagreementException("Gateway is not connected.")
        if not self.user:
            raise DisagreementException("Client user unavailable.")
        assert self.user is not None
        user_id = self.user.id

        if guild_id in self._voice_clients:
            return self._voice_clients[guild_id]

        payload = {
            "op": GatewayOpcode.VOICE_STATE_UPDATE,
            "d": {
                "guild_id": str(guild_id),
                "channel_id": str(channel_id),
                "self_mute": self_mute,
                "self_deaf": self_deaf,
            },
        }
        await self._gateway._send_json(payload)  # type: ignore[attr-defined]

        server = await self.wait_for(
            "VOICE_SERVER_UPDATE",
            check=lambda d: d.get("guild_id") == str(guild_id),
            timeout=10,
        )
        state = await self.wait_for(
            "VOICE_STATE_UPDATE",
            check=lambda d, uid=user_id: d.get("guild_id") == str(guild_id)
            and d.get("user_id") == str(uid),
            timeout=10,
        )

        endpoint = f"wss://{server['endpoint']}?v=10"
        token = server["token"]
        session_id = state["session_id"]

        voice = VoiceClient(
            endpoint,
            session_id,
            token,
            int(guild_id),
            int(self.user.id),
            verbose=self.verbose,
        )
        await voice.connect()
        self._voice_clients[guild_id] = voice
        return voice

    async def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        """|coro| Add a reaction to a message."""

        await self.create_reaction(channel_id, message_id, emoji)

    async def remove_reaction(
        self, channel_id: str, message_id: str, emoji: str
    ) -> None:
        """|coro| Remove the bot's reaction from a message."""

        await self.delete_reaction(channel_id, message_id, emoji)

    async def clear_reactions(self, channel_id: str, message_id: str) -> None:
        """|coro| Remove all reactions from a message."""

        if self._closed:
            raise DisagreementException("Client is closed.")

        await self._http.clear_reactions(channel_id, message_id)

    async def create_reaction(
        self, channel_id: str, message_id: str, emoji: str
    ) -> None:
        """|coro| Add a reaction to a message."""

        if self._closed:
            raise DisagreementException("Client is closed.")

        await self._http.create_reaction(channel_id, message_id, emoji)

        user_id = getattr(getattr(self, "user", None), "id", None)
        payload = {
            "user_id": user_id,
            "channel_id": channel_id,
            "message_id": message_id,
            "emoji": {"name": emoji, "id": None},
        }
        if hasattr(self, "_event_dispatcher"):
            await self._event_dispatcher.dispatch("MESSAGE_REACTION_ADD", payload)

    async def delete_reaction(
        self, channel_id: str, message_id: str, emoji: str
    ) -> None:
        """|coro| Remove the bot's reaction from a message."""

        if self._closed:
            raise DisagreementException("Client is closed.")

        await self._http.delete_reaction(channel_id, message_id, emoji)

        user_id = getattr(getattr(self, "user", None), "id", None)
        payload = {
            "user_id": user_id,
            "channel_id": channel_id,
            "message_id": message_id,
            "emoji": {"name": emoji, "id": None},
        }
        if hasattr(self, "_event_dispatcher"):
            await self._event_dispatcher.dispatch("MESSAGE_REACTION_REMOVE", payload)

    async def get_reactions(
        self, channel_id: str, message_id: str, emoji: str
    ) -> List["User"]:
        """|coro| Return the users who reacted with the given emoji."""

        if self._closed:
            raise DisagreementException("Client is closed.")

        users_data = await self._http.get_reactions(channel_id, message_id, emoji)
        return [self.parse_user(u) for u in users_data]

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        *,
        content: Optional[str] = None,
        embed: Optional["Embed"] = None,
        embeds: Optional[List["Embed"]] = None,
        components: Optional[List["ActionRow"]] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
        flags: Optional[int] = None,
        view: Optional["View"] = None,
    ) -> "Message":
        """Edits a previously sent message."""

        if self._closed:
            raise DisagreementException("Client is closed.")

        if embed and embeds:
            raise ValueError("Cannot provide both embed and embeds.")
        if components and view:
            raise ValueError("Cannot provide both 'components' and 'view'.")

        final_embeds_payload: Optional[List[Dict[str, Any]]] = None
        if embed:
            final_embeds_payload = [embed.to_dict()]
        elif embeds:
            final_embeds_payload = [e.to_dict() for e in embeds]

        components_payload: Optional[List[Dict[str, Any]]] = None
        if view:
            await view._start(self)
            components_payload = view.to_components_payload()
        elif components:
            components_payload = [c.to_dict() for c in components]

        payload: Dict[str, Any] = {}
        if content is not None:
            payload["content"] = content
        if final_embeds_payload is not None:
            payload["embeds"] = final_embeds_payload
        if components_payload is not None:
            payload["components"] = components_payload
        if allowed_mentions is not None:
            payload["allowed_mentions"] = allowed_mentions
        if flags is not None:
            payload["flags"] = flags

        message_data = await self._http.edit_message(
            channel_id=channel_id,
            message_id=message_id,
            payload=payload,
        )

        if view:
            view.message_id = message_data["id"]
            self._views[message_data["id"]] = view

        return self.parse_message(message_data)

    def get_guild(self, guild_id: Snowflake) -> Optional["Guild"]:
        """Returns a guild from the internal cache.

        Use :meth:`fetch_guild` to retrieve it from Discord if it's not cached.
        """

        return self._guilds.get(guild_id)

    def get_channel(self, channel_id: Snowflake) -> Optional["Channel"]:
        """Returns a channel from the internal cache."""

        return self._channels.get(channel_id)

    def get_message(self, message_id: Snowflake) -> Optional["Message"]:
        """Returns a message from the internal cache."""

        return self._messages.get(message_id)

    async def fetch_guild(self, guild_id: Snowflake) -> Optional["Guild"]:
        """Fetches a guild by ID from Discord and caches it."""

        if self._closed:
            raise DisagreementException("Client is closed.")

        cached_guild = self._guilds.get(guild_id)
        if cached_guild:
            return cached_guild

        try:
            guild_data = await self._http.get_guild(guild_id)
            return self.parse_guild(guild_data)
        except DisagreementException as e:
            print(f"Failed to fetch guild {guild_id}: {e}")
            return None

    async def fetch_channel(self, channel_id: Snowflake) -> Optional["Channel"]:
        """Fetches a channel from Discord by its ID and updates the cache."""

        if self._closed:
            raise DisagreementException("Client is closed.")

        try:
            channel_data = await self._http.get_channel(channel_id)
            if not channel_data:
                return None

            from .models import channel_factory

            channel = channel_factory(channel_data, self)

            self._channels[channel.id] = channel
            return channel

        except DisagreementException as e:  # Includes HTTPException
            print(f"Failed to fetch channel {channel_id}: {e}")
            return None

    async def create_webhook(
        self, channel_id: Snowflake, payload: Dict[str, Any]
    ) -> "Webhook":
        """|coro| Create a webhook in the given channel."""

        if self._closed:
            raise DisagreementException("Client is closed.")

        data = await self._http.create_webhook(channel_id, payload)
        return self.parse_webhook(data)

    async def edit_webhook(
        self, webhook_id: Snowflake, payload: Dict[str, Any]
    ) -> "Webhook":
        """|coro| Edit an existing webhook."""

        if self._closed:
            raise DisagreementException("Client is closed.")

        data = await self._http.edit_webhook(webhook_id, payload)
        return self.parse_webhook(data)

    async def delete_webhook(self, webhook_id: Snowflake) -> None:
        """|coro| Delete a webhook by ID."""

        if self._closed:
            raise DisagreementException("Client is closed.")

        await self._http.delete_webhook(webhook_id)

    # --- Application Command Methods ---
    async def process_interaction(self, interaction: Interaction) -> None:
        """Internal method to process an interaction from the gateway."""

        if hasattr(self, "on_interaction_create"):
            asyncio.create_task(self.on_interaction_create(interaction))
        # Route component interactions to the appropriate View
        if (
            interaction.type == InteractionType.MESSAGE_COMPONENT
            and interaction.message
        ):
            view = self._views.get(interaction.message.id)
            if view:
                asyncio.create_task(view._dispatch(interaction))
                return

        await self.app_command_handler.process_interaction(interaction)

    async def sync_application_commands(
        self, guild_id: Optional[Snowflake] = None
    ) -> None:
        """Synchronizes application commands with Discord."""

        if not self.application_id:
            print(
                "Warning: Cannot sync application commands, application_id is not set. "
                "Ensure the client is connected and READY."
            )
            return
        if not self.is_ready():
            print(
                "Warning: Client is not ready. Waiting for client to be ready before syncing commands."
            )
            await self.wait_until_ready()
            if not self.application_id:
                print(
                    "Error: application_id still not set after client is ready. Cannot sync commands."
                )
                return

        await self.app_command_handler.sync_commands(
            application_id=self.application_id, guild_id=guild_id
        )

    async def on_interaction_create(self, interaction: Interaction) -> None:
        """|coro| Called when an interaction is created."""

        pass

    async def on_presence_update(self, presence) -> None:
        """|coro| Called when a user's presence is updated."""

        pass

    async def on_typing_start(self, typing) -> None:
        """|coro| Called when a user starts typing in a channel."""

        pass

    async def on_app_command_error(
        self, context: AppCommandContext, error: Exception
    ) -> None:
        """Default error handler for application commands."""

        print(
            f"Error in application command '{context.command.name if context.command else 'unknown'}': {error}"
        )
        try:
            if not context._responded:
                await context.send(
                    "An error occurred while running this command.", ephemeral=True
                )
        except Exception as e:
            print(f"Failed to send error message for app command: {e}")

    async def on_error(
        self, event_method: str, exc: Exception, *args: Any, **kwargs: Any
    ) -> None:
        """Default event listener error handler."""

        print(f"Unhandled exception in event listener for '{event_method}':")
        print(f"{type(exc).__name__}: {exc}")


class AutoShardedClient(Client):
    """A :class:`Client` that automatically determines the shard count.

    If ``shard_count`` is not provided, the client will query the Discord API
    via :meth:`HTTPClient.get_gateway_bot` for the recommended shard count and
    use that when connecting.
    """

    async def connect(self, reconnect: bool = True) -> None:  # type: ignore[override]
        if self.shard_count is None:
            data = await self._http.get_gateway_bot()
            self.shard_count = data.get("shards", 1)

        await super().connect(reconnect=reconnect)
