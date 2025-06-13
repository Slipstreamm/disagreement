from __future__ import annotations

import asyncio
import logging
import inspect
from typing import (
    TYPE_CHECKING,
    Optional,
    List,
    Dict,
    Any,
    Union,
    Callable,
    Awaitable,
    Tuple,
    get_origin,
    get_args,
)

from .view import StringView
from .errors import (
    CommandError,
    CommandNotFound,
    BadArgument,
    MissingRequiredArgument,
    ArgumentParsingError,
    CheckFailure,
    CommandInvokeError,
)
from .converters import Greedy, run_converters, DEFAULT_CONVERTERS, Converter
from disagreement.typing import Typing

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .cog import Cog
    from disagreement.client import Client
    from disagreement.models import Message, User


class GroupMixin:
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.commands: Dict[str, "Command"] = {}
        self.name: str = ""

    def command(
        self, **attrs: Any
    ) -> Callable[[Callable[..., Awaitable[None]]], "Command"]:
        def decorator(func: Callable[..., Awaitable[None]]) -> "Command":
            cmd = Command(func, **attrs)
            cmd.cog = getattr(self, "cog", None)
            self.add_command(cmd)
            return cmd

        return decorator

    def group(
        self, **attrs: Any
    ) -> Callable[[Callable[..., Awaitable[None]]], "Group"]:
        def decorator(func: Callable[..., Awaitable[None]]) -> "Group":
            cmd = Group(func, **attrs)
            cmd.cog = getattr(self, "cog", None)
            self.add_command(cmd)
            return cmd

        return decorator

    def add_command(self, command: "Command") -> None:
        if command.name in self.commands:
            raise ValueError(
                f"Command '{command.name}' is already registered in group '{self.name}'."
            )
        self.commands[command.name.lower()] = command
        for alias in command.aliases:
            if alias in self.commands:
                logger.warning(
                    f"Alias '{alias}' for command '{command.name}' in group '{self.name}' conflicts with an existing command or alias."
                )
            self.commands[alias.lower()] = command

    def get_command(self, name: str) -> Optional["Command"]:
        return self.commands.get(name.lower())


class Command(GroupMixin):
    """
    Represents a bot command.

    Attributes:
        name (str): The primary name of the command.
        callback (Callable[..., Awaitable[None]]): The coroutine function to execute.
        aliases (List[str]): Alternative names for the command.
        brief (Optional[str]): A short description for help commands.
        description (Optional[str]): A longer description for help commands.
        cog (Optional['Cog']): Reference to the Cog this command belongs to.
        params (Dict[str, inspect.Parameter]): Cached parameters of the callback.
    """

    def __init__(self, callback: Callable[..., Awaitable[None]], **attrs: Any):
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("Command callback must be a coroutine function.")

        super().__init__(**attrs)
        self.callback: Callable[..., Awaitable[None]] = callback
        self.name: str = attrs.get("name", callback.__name__)
        self.aliases: List[str] = attrs.get("aliases", [])
        self.brief: Optional[str] = attrs.get("brief")
        self.description: Optional[str] = attrs.get("description") or callback.__doc__
        self.cog: Optional["Cog"] = attrs.get("cog")
        self.invoke_without_command: bool = attrs.get("invoke_without_command", False)

        self.params = inspect.signature(callback).parameters
        self.checks: List[Callable[["CommandContext"], Awaitable[bool] | bool]] = []
        if hasattr(callback, "__command_checks__"):
            self.checks.extend(getattr(callback, "__command_checks__"))

        self.max_concurrency: Optional[Tuple[int, str]] = None
        if hasattr(callback, "__max_concurrency__"):
            self.max_concurrency = getattr(callback, "__max_concurrency__")

    def add_check(
        self, predicate: Callable[["CommandContext"], Awaitable[bool] | bool]
    ) -> None:
        self.checks.append(predicate)

    async def _run_checks(self, ctx: "CommandContext") -> None:
        """Runs all cog, local and global checks for the command."""
        from .errors import CheckFailure

        # Run cog-level check first
        if self.cog:
            cog_check = getattr(self.cog, "cog_check", None)
            if cog_check:
                try:
                    result = cog_check(ctx)
                    if inspect.isawaitable(result):
                        result = await result
                    if not result:
                        raise CheckFailure(
                            f"The cog-level check for command '{self.name}' failed."
                        )
                except CheckFailure:
                    raise
                except Exception as e:
                    raise CommandInvokeError(e) from e

        # Run local checks
        for predicate in self.checks:
            result = predicate(ctx)
            if inspect.isawaitable(result):
                result = await result
            if not result:
                raise CheckFailure(f"A local check for command '{self.name}' failed.")

        # Then run global checks from the handler
        if hasattr(ctx.bot, "command_handler"):
            for predicate in ctx.bot.command_handler._global_checks:
                result = predicate(ctx)
                if inspect.isawaitable(result):
                    result = await result
                if not result:
                    raise CheckFailure(
                        f"A global check failed for command '{self.name}'."
                    )

    async def invoke(self, ctx: "CommandContext", *args: Any, **kwargs: Any) -> None:
        await self._run_checks(ctx)

        before_invoke = None
        after_invoke = None

        if self.cog:
            before_invoke = getattr(self.cog, "cog_before_invoke", None)
            after_invoke = getattr(self.cog, "cog_after_invoke", None)

        if before_invoke:
            await before_invoke(ctx)

        try:
            if self.cog:
                await self.callback(self.cog, ctx, *args, **kwargs)
            else:
                await self.callback(ctx, *args, **kwargs)
        finally:
            if after_invoke:
                await after_invoke(ctx)


class Group(Command):
    """A command that can have subcommands."""

    def __init__(self, callback: Callable[..., Awaitable[None]], **attrs: Any):
        super().__init__(callback, **attrs)


PrefixCommand = Command  # Alias for clarity in hybrid commands


class CommandContext:
    """
    Represents the context in which a command is being invoked.
    """

    def __init__(
        self,
        *,
        message: "Message",
        bot: "Client",
        prefix: str,
        command: "Command",
        invoked_with: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        cog: Optional["Cog"] = None,
    ):
        self.message: "Message" = message
        self.bot: "Client" = bot
        self.prefix: str = prefix
        self.command: "Command" = command
        self.invoked_with: str = invoked_with
        self.args: List[Any] = args or []
        self.kwargs: Dict[str, Any] = kwargs or {}
        self.cog: Optional["Cog"] = cog

        self.author: "User" = message.author

    @property
    def guild(self):
        """The guild this command was invoked in."""
        if self.message.guild_id and hasattr(self.bot, "get_guild"):
            return self.bot.get_guild(self.message.guild_id)
        return None

    async def reply(
        self,
        content: Optional[str] = None,
        *,
        mention_author: Optional[bool] = None,
        **kwargs: Any,
    ) -> "Message":
        """Replies to the invoking message.

        Parameters
        ----------
        content: str
            The content to send.
        mention_author: Optional[bool]
            Whether to mention the author in the reply. If ``None`` the
            client's :attr:`mention_replies` value is used.
        """

        allowed_mentions = kwargs.pop("allowed_mentions", None)
        if mention_author is None:
            mention_author = getattr(self.bot, "mention_replies", False)

        if allowed_mentions is None:
            allowed_mentions = dict(getattr(self.bot, "allowed_mentions", {}) or {})
        else:
            allowed_mentions = dict(allowed_mentions)
        allowed_mentions.setdefault("replied_user", mention_author)

        return await self.bot.send_message(
            channel_id=self.message.channel_id,
            content=content,
            message_reference={
                "message_id": self.message.id,
                "channel_id": self.message.channel_id,
                "guild_id": self.message.guild_id,
            },
            allowed_mentions=allowed_mentions,
            **kwargs,
        )

    async def send(self, content: str, **kwargs: Any) -> "Message":
        return await self.bot.send_message(
            channel_id=self.message.channel_id, content=content, **kwargs
        )

    async def edit(
        self,
        message: Union[str, "Message"],
        *,
        content: Optional[str] = None,
        **kwargs: Any,
    ) -> "Message":
        """Edits a message previously sent by the bot."""

        message_id = message if isinstance(message, str) else message.id
        return await self.bot.edit_message(
            channel_id=self.message.channel_id,
            message_id=message_id,
            content=content,
            **kwargs,
        )

    def typing(self) -> "Typing":
        """Return a typing context manager for this context's channel."""

        return self.bot.typing(self.message.channel_id)


class CommandHandler:
    """
    Manages command registration, parsing, and dispatching.
    """

    def __init__(
        self,
        client: "Client",
        prefix: Union[
            str, List[str], Callable[["Client", "Message"], Union[str, List[str]]]
        ],
    ):
        self.client: "Client" = client
        self.prefix: Union[
            str, List[str], Callable[["Client", "Message"], Union[str, List[str]]]
        ] = prefix
        self.commands: Dict[str, Command] = {}
        self.cogs: Dict[str, "Cog"] = {}
        self._concurrency: Dict[str, Dict[str, int]] = {}
        self._global_checks: List[
            Callable[["CommandContext"], Awaitable[bool] | bool]
        ] = []

        from .help import HelpCommand

        self.add_command(HelpCommand(self))

    def add_check(
        self, predicate: Callable[["CommandContext"], Awaitable[bool] | bool]
    ) -> None:
        """Adds a global check to the command handler."""
        self._global_checks.append(predicate)

    def add_command(self, command: Command) -> None:
        if command.name in self.commands:
            raise ValueError(f"Command '{command.name}' is already registered.")

        self.commands[command.name.lower()] = command
        for alias in command.aliases:
            if alias in self.commands:
                logger.warning(
                    "Alias '%s' for command '%s' conflicts with an existing command or alias.",
                    alias,
                    command.name,
                )
            self.commands[alias.lower()] = command

        if isinstance(command, Group):
            for sub_cmd in command.commands.values():
                if sub_cmd.name in self.commands:
                    logger.warning(
                        "Subcommand '%s' of group '%s' conflicts with a top-level command.",
                        sub_cmd.name,
                        command.name,
                    )

    def remove_command(self, name: str) -> Optional[Command]:
        command = self.commands.pop(name.lower(), None)
        if command:
            for alias in command.aliases:
                self.commands.pop(alias.lower(), None)
        return command

    def get_command(self, name: str) -> Optional[Command]:
        return self.commands.get(name.lower())

    def add_cog(self, cog_to_add: "Cog") -> None:
        from .cog import Cog

        if not isinstance(cog_to_add, Cog):
            raise TypeError("Argument must be a subclass of Cog.")

        if cog_to_add.cog_name in self.cogs:
            raise ValueError(
                f"Cog with name '{cog_to_add.cog_name}' is already registered."
            )

        self.cogs[cog_to_add.cog_name] = cog_to_add

        for cmd in cog_to_add.get_commands():
            self.add_command(cmd)

        if hasattr(self.client, "_event_dispatcher"):
            for event_name, callback in cog_to_add.get_listeners():
                self.client._event_dispatcher.register(event_name.upper(), callback)
        else:
            logger.warning(
                "Client does not have '_event_dispatcher'. Listeners for cog '%s' not registered.",
                cog_to_add.cog_name,
            )

        if hasattr(cog_to_add, "cog_load") and inspect.iscoroutinefunction(
            cog_to_add.cog_load
        ):
            asyncio.create_task(cog_to_add.cog_load())

        logger.info("Cog '%s' added.", cog_to_add.cog_name)

    def remove_cog(self, cog_name: str) -> Optional["Cog"]:
        cog_to_remove = self.cogs.pop(cog_name, None)
        if cog_to_remove:
            for cmd in cog_to_remove.get_commands():
                self.remove_command(cmd.name)

            if hasattr(self.client, "_event_dispatcher"):
                for event_name, callback in cog_to_remove.get_listeners():
                    logger.debug(
                        "Listener '%s' for event '%s' from cog '%s' needs manual unregistration logic in EventDispatcher.",
                        callback.__name__,
                        event_name,
                        cog_name,
                    )

            if hasattr(cog_to_remove, "cog_unload") and inspect.iscoroutinefunction(
                cog_to_remove.cog_unload
            ):
                asyncio.create_task(cog_to_remove.cog_unload())

            cog_to_remove._eject()
            logger.info("Cog '%s' removed.", cog_name)
        return cog_to_remove

    def _acquire_concurrency(self, ctx: CommandContext) -> None:
        mc = getattr(ctx.command, "max_concurrency", None)
        if not mc:
            return
        limit, scope = mc
        if scope == "user":
            key = ctx.author.id
        elif scope == "guild":
            key = ctx.message.guild_id or ctx.author.id
        else:
            key = "global"
        buckets = self._concurrency.setdefault(ctx.command.name, {})
        current = buckets.get(key, 0)
        if current >= limit:
            from .errors import MaxConcurrencyReached

            raise MaxConcurrencyReached(limit)
        buckets[key] = current + 1

    def _release_concurrency(self, ctx: CommandContext) -> None:
        mc = getattr(ctx.command, "max_concurrency", None)
        if not mc:
            return
        _, scope = mc
        if scope == "user":
            key = ctx.author.id
        elif scope == "guild":
            key = ctx.message.guild_id or ctx.author.id
        else:
            key = "global"
        buckets = self._concurrency.get(ctx.command.name)
        if not buckets:
            return
        current = buckets.get(key, 0)
        if current <= 1:
            buckets.pop(key, None)
        else:
            buckets[key] = current - 1
        if not buckets:
            self._concurrency.pop(ctx.command.name, None)

    async def get_prefix(self, message: "Message") -> Union[str, List[str], None]:
        if callable(self.prefix):
            if inspect.iscoroutinefunction(self.prefix):
                return await self.prefix(self.client, message)
            else:
                return self.prefix(self.client, message)  # type: ignore
        return self.prefix

    async def _parse_arguments(
        self, command: Command, ctx: CommandContext, view: StringView
    ) -> Tuple[List[Any], Dict[str, Any]]:
        args_list = []
        kwargs_dict = {}
        params_to_parse = list(command.params.values())

        if params_to_parse and params_to_parse[0].name == "self" and command.cog:
            params_to_parse.pop(0)
        if params_to_parse and params_to_parse[0].name == "ctx":
            params_to_parse.pop(0)

        for param in params_to_parse:
            view.skip_whitespace()
            final_value_for_param: Any = inspect.Parameter.empty

            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                while not view.eof:
                    view.skip_whitespace()
                    if view.eof:
                        break
                    word = view.get_word()
                    if word or not view.eof:
                        args_list.append(word)
                    elif view.eof:
                        break
                break

            arg_str_value: Optional[str] = (
                None  # Holds the raw string for current param
            )

            annotation = param.annotation
            if inspect.isclass(annotation) and issubclass(annotation, Greedy):
                greedy_values = []
                converter_type = annotation.converter
                while not view.eof:
                    view.skip_whitespace()
                    if view.eof:
                        break
                    start = view.index
                    if view.buffer[view.index] == '"':
                        arg_str_value = view.get_quoted_string()
                        if arg_str_value == "" and view.buffer[view.index] == '"':
                            raise BadArgument(
                                f"Unterminated quoted string for argument '{param.name}'."
                            )
                    else:
                        arg_str_value = view.get_word()
                    try:
                        converted = await run_converters(
                            ctx, converter_type, arg_str_value
                        )
                    except BadArgument:
                        view.index = start
                        break
                    greedy_values.append(converted)
                final_value_for_param = greedy_values
                arg_str_value = None
            elif view.eof:  # No more input string
                if param.default is not inspect.Parameter.empty:
                    final_value_for_param = param.default
                elif param.kind != inspect.Parameter.VAR_KEYWORD:
                    raise MissingRequiredArgument(param.name)
                else:  # VAR_KEYWORD at EOF is fine
                    break
            else:  # Input available
                is_last_pos_str_greedy = (
                    param == params_to_parse[-1]
                    and param.annotation is str
                    and param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                )

                if is_last_pos_str_greedy:
                    arg_str_value = view.read_rest().strip()
                    if (
                        not arg_str_value
                        and param.default is not inspect.Parameter.empty
                    ):
                        final_value_for_param = param.default
                    else:  # Includes empty string if that's what's left
                        final_value_for_param = arg_str_value
                else:  # Not greedy, or not string, or not last positional
                    if view.buffer[view.index] == '"':
                        arg_str_value = view.get_quoted_string()
                        if arg_str_value == "" and view.buffer[view.index] == '"':
                            raise BadArgument(
                                f"Unterminated quoted string for argument '{param.name}'."
                            )
                    else:
                        arg_str_value = view.get_word()

                # If final_value_for_param was not set by greedy logic, try conversion
                if final_value_for_param is inspect.Parameter.empty:
                    if arg_str_value is None:
                        if param.default is not inspect.Parameter.empty:
                            final_value_for_param = param.default
                        else:
                            raise MissingRequiredArgument(param.name)
                    else:  # We have an arg_str_value (could be empty string "" from quotes)
                        annotation = param.annotation
                        origin = get_origin(annotation)

                        if origin is Union:  # Handles Optional[T] and Union[T1, T2]
                            union_args = get_args(annotation)
                            is_optional = (
                                len(union_args) == 2 and type(None) in union_args
                            )

                            converted_for_union = False
                            last_err_union: Optional[BadArgument] = None
                            for t_arg in union_args:
                                if t_arg is type(None):
                                    continue
                                try:
                                    final_value_for_param = await run_converters(
                                        ctx, t_arg, arg_str_value
                                    )
                                    converted_for_union = True
                                    break
                                except BadArgument as e:
                                    last_err_union = e

                            if not converted_for_union:
                                if (
                                    is_optional and param.default is None
                                ):  # Special handling for Optional[T] if conversion failed
                                    # If arg_str_value was "" and type was Optional[str], StringConverter would return ""
                                    # If arg_str_value was "" and type was Optional[int], BadArgument would be raised.
                                    # This path is for when all actual types in Optional[T] fail conversion.
                                    # If default is None, we can assign None.
                                    final_value_for_param = None
                                elif last_err_union:
                                    raise last_err_union
                                else:
                                    raise BadArgument(
                                        f"Could not convert '{arg_str_value}' to any of {union_args} for param '{param.name}'."
                                    )
                        elif annotation is inspect.Parameter.empty or annotation is str:
                            final_value_for_param = arg_str_value
                        else:  # Standard type hint
                            final_value_for_param = await run_converters(
                                ctx, annotation, arg_str_value
                            )

            # Final check if value was resolved
            if final_value_for_param is inspect.Parameter.empty:
                if param.default is not inspect.Parameter.empty:
                    final_value_for_param = param.default
                elif param.kind != inspect.Parameter.VAR_KEYWORD:
                    # This state implies an issue if required and no default, and no input was parsed.
                    raise MissingRequiredArgument(
                        f"Parameter '{param.name}' could not be resolved."
                    )

            # Assign to args_list or kwargs_dict if a value was determined
            if final_value_for_param is not inspect.Parameter.empty:
                if (
                    param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                    or param.kind == inspect.Parameter.POSITIONAL_ONLY
                ):
                    args_list.append(final_value_for_param)
                elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                    kwargs_dict[param.name] = final_value_for_param

        return args_list, kwargs_dict

    async def process_commands(self, message: "Message") -> None:
        if not message.content:
            return

        prefix_to_use = await self.get_prefix(message)
        if not prefix_to_use:
            return

        actual_prefix: Optional[str] = None
        if isinstance(prefix_to_use, list):
            for p in prefix_to_use:
                if message.content.startswith(p):
                    actual_prefix = p
                    break
            if not actual_prefix:
                return
        elif isinstance(prefix_to_use, str):
            if message.content.startswith(prefix_to_use):
                actual_prefix = prefix_to_use
            else:
                return
        else:
            return

        if actual_prefix is None:
            return

        content_without_prefix = message.content[len(actual_prefix) :]
        view = StringView(content_without_prefix)

        command_name = view.get_word()
        if not command_name:
            return

        command = self.get_command(command_name)
        if not command:
            return

        invoked_with = command_name
        original_command = command

        if isinstance(command, Group):
            view.skip_whitespace()
            potential_subcommand = view.get_word()
            if potential_subcommand:
                subcommand = command.get_command(potential_subcommand)
                if subcommand:
                    command = subcommand
                    invoked_with += f" {potential_subcommand}"
                elif command.invoke_without_command:
                    view.index -= len(potential_subcommand) + view.previous
                else:
                    raise CommandNotFound(
                        f"Subcommand '{potential_subcommand}' not found."
                    )

        ctx = CommandContext(
            message=message,
            bot=self.client,
            prefix=actual_prefix,
            command=command,
            invoked_with=invoked_with,
            cog=command.cog,
        )

        try:
            parsed_args, parsed_kwargs = await self._parse_arguments(command, ctx, view)
            ctx.args = parsed_args
            ctx.kwargs = parsed_kwargs
            self._acquire_concurrency(ctx)
            try:
                await command.invoke(ctx, *parsed_args, **parsed_kwargs)
            finally:
                self._release_concurrency(ctx)
        except CommandError as e:
            logger.error("Command error for '%s': %s", original_command.name, e)
            if hasattr(self.client, "on_command_error"):
                await self.client.on_command_error(ctx, e)
        except Exception as e:
            logger.error(
                "Unexpected error invoking command '%s': %s", original_command.name, e
            )
            exc = CommandInvokeError(e)
            if hasattr(self.client, "on_command_error"):
                await self.client.on_command_error(ctx, exc)
        else:
            if hasattr(self.client, "on_command_completion"):
                await self.client.on_command_completion(ctx)
