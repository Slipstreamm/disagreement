# disagreement/ext/app_commands/handler.py

import inspect
from typing import (
    TYPE_CHECKING,
    Dict,
    Optional,
    List,
    Any,
    Tuple,
    Union,
    get_origin,
    get_args,
    Literal,
)

if TYPE_CHECKING:
    from disagreement.client import Client
    from disagreement.interactions import Interaction, ResolvedData, Snowflake
    from disagreement.enums import (
        ApplicationCommandType,
        ApplicationCommandOptionType,
        InteractionType,
    )
    from .commands import (
        AppCommand,
        SlashCommand,
        UserCommand,
        MessageCommand,
        AppCommandGroup,
    )
    from .context import AppCommandContext
    from disagreement.models import (
        User,
        Member,
        Role,
        Attachment,
        Message,
    )  # For resolved data

    # Channel models would also go here

# Placeholder for models not yet fully defined or imported
if not TYPE_CHECKING:
    from disagreement.enums import (
        ApplicationCommandType,
        ApplicationCommandOptionType,
        InteractionType,
    )
    from .commands import (
        AppCommand,
        SlashCommand,
        UserCommand,
        MessageCommand,
        AppCommandGroup,
    )
    from .context import AppCommandContext

    User = Any
    Member = Any
    Role = Any
    Attachment = Any
    Channel = Any
    Message = Any


class AppCommandHandler:
    """
    Manages application command registration, parsing, and dispatching.
    """

    def __init__(self, client: "Client"):
        self.client: "Client" = client
        # Store commands: key could be (name, type) for global, or (name, type, guild_id) for guild-specific
        # For simplicity, let's start with a flat structure and refine if needed for guild commands.
        # A more robust system might have separate dicts for global and guild commands.
        self._slash_commands: Dict[str, SlashCommand] = {}
        self._user_commands: Dict[str, UserCommand] = {}
        self._message_commands: Dict[str, MessageCommand] = {}
        self._app_command_groups: Dict[str, AppCommandGroup] = {}
        self._converter_registry: Dict[type, type] = {}

    def add_command(self, command: Union["AppCommand", "AppCommandGroup"]) -> None:
        """Adds an application command or a command group to the handler."""
        if isinstance(command, AppCommandGroup):
            if command.name in self._app_command_groups:
                raise ValueError(
                    f"AppCommandGroup '{command.name}' is already registered."
                )
            self._app_command_groups[command.name] = command
            return

        if isinstance(command, SlashCommand):
            if command.name in self._slash_commands:
                raise ValueError(
                    f"SlashCommand '{command.name}' is already registered."
                )
            self._slash_commands[command.name] = command
            return

        if isinstance(command, UserCommand):
            if command.name in self._user_commands:
                raise ValueError(f"UserCommand '{command.name}' is already registered.")
            self._user_commands[command.name] = command
            return

        if isinstance(command, MessageCommand):
            if command.name in self._message_commands:
                raise ValueError(
                    f"MessageCommand '{command.name}' is already registered."
                )
            self._message_commands[command.name] = command
            return

        if isinstance(command, AppCommand):
            # Fallback for plain AppCommand objects
            if command.type == ApplicationCommandType.CHAT_INPUT:
                if command.name in self._slash_commands:
                    raise ValueError(
                        f"SlashCommand '{command.name}' is already registered."
                    )
                self._slash_commands[command.name] = command  # type: ignore
            elif command.type == ApplicationCommandType.USER:
                if command.name in self._user_commands:
                    raise ValueError(
                        f"UserCommand '{command.name}' is already registered."
                    )
                self._user_commands[command.name] = command  # type: ignore
            elif command.type == ApplicationCommandType.MESSAGE:
                if command.name in self._message_commands:
                    raise ValueError(
                        f"MessageCommand '{command.name}' is already registered."
                    )
                self._message_commands[command.name] = command  # type: ignore
            else:
                raise TypeError(
                    f"Unsupported command type: {command.type} for '{command.name}'"
                )
        else:
            raise TypeError("Can only add AppCommand or AppCommandGroup instances.")

    def remove_command(
        self, name: str
    ) -> Optional[Union["AppCommand", "AppCommandGroup"]]:
        """Removes an application command or group by name."""
        if name in self._slash_commands:
            return self._slash_commands.pop(name)
        if name in self._user_commands:
            return self._user_commands.pop(name)
        if name in self._message_commands:
            return self._message_commands.pop(name)
        if name in self._app_command_groups:
            return self._app_command_groups.pop(name)
        return None

    def register_converter(self, annotation: type, converter_cls: type) -> None:
        """Register a custom converter class for a type annotation."""
        self._converter_registry[annotation] = converter_cls

    def get_converter(self, annotation: type) -> Optional[type]:
        """Retrieve a registered converter class for a type annotation."""
        return self._converter_registry.get(annotation)

    def get_command(
        self,
        name: str,
        command_type: "ApplicationCommandType",
        interaction_options: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional["AppCommand"]:
        """Retrieves a command of a specific type."""
        if command_type == ApplicationCommandType.CHAT_INPUT:
            if not interaction_options:
                return self._slash_commands.get(name)

            # Handle subcommands/groups
            current_options = interaction_options
            target_command_or_group: Optional[Union[AppCommand, AppCommandGroup]] = (
                self._app_command_groups.get(name)
            )

            if not target_command_or_group:
                return self._slash_commands.get(name)

            final_command: Optional[AppCommand] = None

            while current_options:
                opt_data = current_options[0]
                opt_name = opt_data.get("name")
                opt_type = (
                    ApplicationCommandOptionType(opt_data["type"])
                    if opt_data.get("type")
                    else None
                )

                if not opt_name or not isinstance(
                    target_command_or_group, AppCommandGroup
                ):
                    break

                next_target = target_command_or_group.get_command(opt_name)

                if isinstance(next_target, AppCommand) and (
                    opt_type == ApplicationCommandOptionType.SUB_COMMAND
                    or not opt_data.get("options")
                ):
                    final_command = next_target
                    break
                elif (
                    isinstance(next_target, AppCommandGroup)
                    and opt_type == ApplicationCommandOptionType.SUB_COMMAND_GROUP
                ):
                    target_command_or_group = next_target
                    current_options = opt_data.get("options", [])
                    if not current_options:
                        break
                else:
                    break

            return final_command

        if command_type == ApplicationCommandType.USER:
            return self._user_commands.get(name)

        if command_type == ApplicationCommandType.MESSAGE:
            return self._message_commands.get(name)

        return None

    async def _resolve_option_value(
        self,
        value: Any,
        expected_type: Any,
        resolved_data: Optional["ResolvedData"],
        guild_id: Optional["Snowflake"],
    ) -> Any:
        """
        Resolves an option value to the expected Python type using resolved_data.
        """
        converter_cls = self.get_converter(expected_type)
        if converter_cls:
            try:
                init_params = inspect.signature(converter_cls.__init__).parameters
                if "client" in init_params:
                    converter_instance = converter_cls(client=self.client)  # type: ignore[arg-type]
                else:
                    converter_instance = converter_cls()
                return await converter_instance.convert(None, value)  # type: ignore[arg-type]
            except Exception:
                pass

        # This is a simplified resolver. A more robust one would use converters.
        if resolved_data:
            if expected_type is User or expected_type.__name__ == "User":
                return resolved_data.users.get(value) if resolved_data.users else None

            if expected_type is Member or expected_type.__name__ == "Member":
                member_obj = (
                    resolved_data.members.get(value) if resolved_data.members else None
                )
                if member_obj:
                    if (
                        hasattr(member_obj, "username")
                        and not member_obj.username
                        and resolved_data.users
                    ):
                        user_obj = resolved_data.users.get(value)
                        if user_obj:
                            member_obj.username = user_obj.username
                            member_obj.discriminator = user_obj.discriminator
                            member_obj.avatar = user_obj.avatar
                            member_obj.bot = user_obj.bot
                            member_obj.user = user_obj  # type: ignore[attr-defined]
                    return member_obj
                return None
            if expected_type is Role or expected_type.__name__ == "Role":
                return resolved_data.roles.get(value) if resolved_data.roles else None
            if expected_type is Attachment or expected_type.__name__ == "Attachment":
                return (
                    resolved_data.attachments.get(value)
                    if resolved_data.attachments
                    else None
                )
            if expected_type is Message or expected_type.__name__ == "Message":
                return (
                    resolved_data.messages.get(value)
                    if resolved_data.messages
                    else None
                )
            if "Channel" in expected_type.__name__:
                return (
                    resolved_data.channels.get(value)
                    if resolved_data.channels
                    else None
                )

        # For basic types, Discord already sends them correctly (string, int, bool, float)
        if isinstance(value, expected_type):
            return value
        try:  # Attempt direct conversion for basic types if Discord sent string for int/float/bool
            if expected_type is int:
                return int(value)
            if expected_type is float:
                return float(value)
            if expected_type is bool:  # Discord sends true/false
                if isinstance(value, str):
                    return value.lower() == "true"
                return bool(value)
        except (ValueError, TypeError):
            pass  # Conversion failed
        return value  # Return as is if no specific resolution or conversion applied

    async def _resolve_value(
        self,
        value: Any,
        expected_type: Any,
        resolved_data: Optional["ResolvedData"],
        guild_id: Optional["Snowflake"],
    ) -> Any:
        """Public wrapper around ``_resolve_option_value`` used by tests."""

        return await self._resolve_option_value(
            value=value,
            expected_type=expected_type,
            resolved_data=resolved_data,
            guild_id=guild_id,
        )

    async def _parse_interaction_options(
        self,
        command_params: Dict[str, inspect.Parameter],  # From command.params
        interaction_options: Optional[List[Dict[str, Any]]],
        resolved_data: Optional["ResolvedData"],
        guild_id: Optional["Snowflake"],
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Parses options from an interaction payload and maps them to command function arguments.
        """
        args_list: List[Any] = []
        kwargs_dict: Dict[str, Any] = {}

        if not interaction_options:  # No options provided in interaction
            # Check if command has required params without defaults
            for name, param in command_params.items():
                if param.default == inspect.Parameter.empty:
                    # This should ideally be caught by Discord if option is marked required
                    raise ValueError(f"Missing required option: {name}")
            return args_list, kwargs_dict

        # Create a dictionary of provided options by name for easier lookup
        provided_options: Dict[str, Any] = {
            opt["name"]: opt["value"] for opt in interaction_options if "value" in opt
        }

        for name, param in command_params.items():
            if name in provided_options:
                raw_value = provided_options[name]
                expected_type = (
                    param.annotation
                    if param.annotation != inspect.Parameter.empty
                    else str
                )

                # Handle Optional[T]
                origin_type = get_origin(expected_type)
                if origin_type is Union:
                    union_args = get_args(expected_type)
                    # Assuming Optional[T] is Union[T, NoneType]
                    non_none_types = [t for t in union_args if t is not type(None)]
                    if len(non_none_types) == 1:
                        expected_type = non_none_types[0]
                    # Else, complex Union, might need more sophisticated handling or default to raw_value/str
                elif origin_type is Literal:
                    literal_args = get_args(expected_type)
                    if literal_args:
                        expected_type = type(literal_args[0])
                    else:
                        expected_type = str

                resolved_value = await self._resolve_option_value(
                    raw_value, expected_type, resolved_data, guild_id
                )

                if (
                    param.kind == inspect.Parameter.KEYWORD_ONLY
                    or param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                ):
                    kwargs_dict[name] = resolved_value
                # Note: Slash commands don't map directly to *args. All options are named.
                # So, we'll primarily use kwargs_dict and then construct args_list based on param order if needed,
                # but Discord sends named options, so direct kwarg usage is more natural.
            elif param.default != inspect.Parameter.empty:
                kwargs_dict[name] = param.default
            else:
                # Required parameter not provided by Discord - this implies an issue with command definition
                # or Discord's validation, as Discord should enforce required options.
                raise ValueError(
                    f"Required option '{name}' not found in interaction payload."
                )

        # Populate args_list based on the order in command_params for positional arguments
        # This assumes that all args that are not keyword-only are passed positionally if present in kwargs_dict
        for name, param in command_params.items():
            if param.kind == inspect.Parameter.POSITIONAL_ONLY or (
                param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                and name in kwargs_dict
            ):
                if name in kwargs_dict:  # Ensure it was resolved or had a default
                    args_list.append(kwargs_dict[name])
                # If it was POSITIONAL_ONLY and not in kwargs_dict, it's an error (already raised)
            elif param.kind == inspect.Parameter.VAR_POSITIONAL:  # *args
                # Slash commands don't map to *args well. This would be empty.
                pass

        # Filter kwargs_dict to only include actual KEYWORD_ONLY or POSITIONAL_OR_KEYWORD params
        # that were not used for args_list (if strict positional/keyword separation is desired).
        # For slash commands, it's simpler to pass all resolved named options as kwargs.
        final_kwargs = {
            k: v
            for k, v in kwargs_dict.items()
            if k in command_params
            and command_params[k].kind != inspect.Parameter.POSITIONAL_ONLY
        }

        # For simplicity with slash commands, let's assume all resolved options are passed via kwargs
        # and the command signature is primarily (self, ctx, **options) or (ctx, **options)
        # or (self, ctx, option1, option2) where names match.
        # The AppCommand.invoke will handle passing them.
        # The current args_list and final_kwargs might be redundant if invoke just uses **final_kwargs.
        # Let's return kwargs_dict directly for now, and AppCommand.invoke can map them.

        return [], kwargs_dict  # Return empty args, all in kwargs for now.

    async def dispatch_app_command_error(
        self, context: "AppCommandContext", error: Exception
    ) -> None:
        """Dispatches an app command error to the client if implemented."""
        if hasattr(self.client, "on_app_command_error"):
            await self.client.on_app_command_error(context, error)

    async def process_interaction(self, interaction: "Interaction") -> None:
        """Processes an incoming interaction."""
        if interaction.type == InteractionType.MODAL_SUBMIT:
            callback = getattr(self.client, "on_modal_submit", None)
            if callback is not None:
                from typing import Awaitable, Callable, cast

                await cast(Callable[["Interaction"], Awaitable[None]], callback)(
                    interaction
                )
            return

        if interaction.type == InteractionType.APPLICATION_COMMAND_AUTOCOMPLETE:
            callback = getattr(self.client, "on_autocomplete", None)
            if callback is not None:
                from typing import Awaitable, Callable, cast

                await cast(Callable[["Interaction"], Awaitable[None]], callback)(
                    interaction
                )
            return

        if interaction.type != InteractionType.APPLICATION_COMMAND:
            return

        if not interaction.data or not interaction.data.name:
            from .context import AppCommandContext

            ctx = AppCommandContext(
                bot=self.client, interaction=interaction, command=None
            )
            await ctx.send("Command not found.", ephemeral=True)
            return

        command_name = interaction.data.name
        command_type = interaction.data.type or ApplicationCommandType.CHAT_INPUT
        command = self.get_command(
            command_name,
            command_type,
            interaction.data.options if interaction.data else None,
        )

        if not command:
            from .context import AppCommandContext

            ctx = AppCommandContext(
                bot=self.client, interaction=interaction, command=None
            )
            await ctx.send(f"Command '{command_name}' not found.", ephemeral=True)
            return

        # Create context
        from .context import AppCommandContext  # Ensure AppCommandContext is available

        ctx = AppCommandContext(
            bot=self.client, interaction=interaction, command=command
        )

        try:
            # Prepare arguments for the command callback
            # Skip 'self' and 'ctx' from command.params for parsing interaction options
            params_to_parse = {
                name: param
                for name, param in command.params.items()
                if name not in ("self", "ctx")
            }

            if command.type in (
                ApplicationCommandType.USER,
                ApplicationCommandType.MESSAGE,
            ):
                # Context menu commands provide a target_id. Resolve and pass it
                args = []
                kwargs = {}
                if params_to_parse and interaction.data and interaction.data.target_id:
                    first_param = next(iter(params_to_parse.values()))
                    expected = (
                        first_param.annotation
                        if first_param.annotation != inspect.Parameter.empty
                        else str
                    )
                    resolved = await self._resolve_option_value(
                        interaction.data.target_id,
                        expected,
                        interaction.data.resolved,
                        interaction.guild_id,
                    )
                    if first_param.kind in (
                        inspect.Parameter.POSITIONAL_ONLY,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    ):
                        args.append(resolved)
                    else:
                        kwargs[first_param.name] = resolved

                await command.invoke(ctx, *args, **kwargs)
            else:
                parsed_args, parsed_kwargs = await self._parse_interaction_options(
                    command_params=params_to_parse,
                    interaction_options=interaction.data.options,
                    resolved_data=interaction.data.resolved,
                    guild_id=interaction.guild_id,
                )

                await command.invoke(ctx, *parsed_args, **parsed_kwargs)

        except Exception as e:
            print(f"Error invoking app command '{command.name}': {e}")
            await self.dispatch_app_command_error(ctx, e)
            # else:
            #     # Default error reply if no handler on client
            #     try:
            #         await ctx.send(f"An error occurred: {e}", ephemeral=True)
            #     except Exception as send_e:
            #         print(f"Failed to send error message for app command: {send_e}")

    async def sync_commands(
        self, application_id: "Snowflake", guild_id: Optional["Snowflake"] = None
    ) -> None:
        """
        Synchronizes (registers/updates) all application commands with Discord.
        If guild_id is provided, syncs commands for that guild. Otherwise, syncs global commands.
        """
        commands_to_sync: List[Dict[str, Any]] = []

        # Collect commands based on scope (global or specific guild)
        # This needs to be more sophisticated to handle guild_ids on commands/groups

        source_commands = (
            list(self._slash_commands.values())
            + list(self._user_commands.values())
            + list(self._message_commands.values())
            + list(self._app_command_groups.values())
        )

        for cmd_or_group in source_commands:
            # Determine if this command/group should be synced for the current scope
            is_guild_specific_command = (
                cmd_or_group.guild_ids is not None and len(cmd_or_group.guild_ids) > 0
            )

            if guild_id:  # Syncing for a specific guild
                # Skip if not a guild-specific command OR if it's for a different guild
                if not is_guild_specific_command or (
                    cmd_or_group.guild_ids is not None
                    and guild_id not in cmd_or_group.guild_ids
                ):
                    continue
            else:  # Syncing global commands
                if is_guild_specific_command:
                    continue  # Skip guild-specific commands when syncing global

            # Use the to_dict() method from AppCommand or AppCommandGroup
            try:
                payload = cmd_or_group.to_dict()
                commands_to_sync.append(payload)
            except AttributeError:
                print(
                    f"Warning: Command or group '{cmd_or_group.name}' does not have a to_dict() method. Skipping."
                )
            except Exception as e:
                print(
                    f"Error converting command/group '{cmd_or_group.name}' to dict: {e}. Skipping."
                )

        if not commands_to_sync:
            print(
                f"No commands to sync for {'guild ' + str(guild_id) if guild_id else 'global'} scope."
            )
            return

        try:
            if guild_id:
                print(
                    f"Syncing {len(commands_to_sync)} commands for guild {guild_id}..."
                )
                await self.client._http.bulk_overwrite_guild_application_commands(
                    application_id, guild_id, commands_to_sync
                )
            else:
                print(f"Syncing {len(commands_to_sync)} global commands...")
                await self.client._http.bulk_overwrite_global_application_commands(
                    application_id, commands_to_sync
                )
            print("Command sync successful.")
        except Exception as e:
            print(f"Error syncing application commands: {e}")
            # Consider re-raising or specific error handling
