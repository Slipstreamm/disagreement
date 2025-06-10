# disagreement/ext/app_commands/decorators.py

import inspect
import asyncio
from dataclasses import dataclass
from typing import (
    Callable,
    Optional,
    List,
    Dict,
    Any,
    Union,
    Type,
    get_origin,
    get_args,
    TYPE_CHECKING,
    Literal,
    Annotated,
    TypeVar,
    cast,
)

from .commands import (
    SlashCommand,
    UserCommand,
    MessageCommand,
    AppCommand,
    AppCommandGroup,
)
from .hybrid import HybridCommand
from disagreement.interactions import (
    ApplicationCommandOption,
    ApplicationCommandOptionChoice,
    Snowflake,
)
from disagreement.enums import (
    ApplicationCommandOptionType,
    IntegrationType,
    InteractionContextType,
    # Assuming ChannelType will be added to disagreement.enums
)

if TYPE_CHECKING:
    from disagreement.client import Client  # For potential future use
    from disagreement.models import Channel, User

    # Assuming TextChannel, VoiceChannel etc. might be defined or aliased
    # For now, we'll use string comparisons for channel types or rely on a yet-to-be-defined ChannelType enum
    Channel = Any
    Member = Any
    Role = Any
    Attachment = Any
    # from .cog import Cog # Placeholder
else:
    # Runtime fallbacks for optional model classes
    from disagreement.models import Channel

    Client = Any  # type: ignore
    User = Any  # type: ignore
    Member = Any  # type: ignore
    Role = Any  # type: ignore
    Attachment = Any  # type: ignore

# Mapping Python types to Discord ApplicationCommandOptionType
# This will need to be expanded and made more robust.
# Consider using a registry or a more sophisticated type mapping system.
_type_mapping: Dict[Any, ApplicationCommandOptionType] = (
    {  # Changed Type to Any for key due to placeholders
        str: ApplicationCommandOptionType.STRING,
        int: ApplicationCommandOptionType.INTEGER,
        bool: ApplicationCommandOptionType.BOOLEAN,
        float: ApplicationCommandOptionType.NUMBER,  # Discord 'NUMBER' type is for float/double
        User: ApplicationCommandOptionType.USER,
        Channel: ApplicationCommandOptionType.CHANNEL,
        # Placeholders for actual model types from disagreement.models
        # These will be resolved to their actual types when TYPE_CHECKING is False or via isinstance checks
    }
)


# Helper dataclass for storing extra option metadata
@dataclass
class OptionMetadata:
    channel_types: Optional[List[int]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    autocomplete: bool = False


# Ensure these are updated if model names/locations change
if TYPE_CHECKING:
    # _type_mapping[User] = ApplicationCommandOptionType.USER # Already added above
    _type_mapping[Member] = ApplicationCommandOptionType.USER  # Member implies User
    _type_mapping[Role] = ApplicationCommandOptionType.ROLE
    _type_mapping[Attachment] = ApplicationCommandOptionType.ATTACHMENT
    _type_mapping[Channel] = ApplicationCommandOptionType.CHANNEL

# TypeVar for the app command decorator factory
AppCmdType = TypeVar("AppCmdType", bound=AppCommand)


def _extract_options_from_signature(
    func: Callable[..., Any], option_meta: Optional[Dict[str, OptionMetadata]] = None
) -> List[ApplicationCommandOption]:
    """
    Inspects a function signature and generates ApplicationCommandOption list.
    """
    options: List[ApplicationCommandOption] = []
    params = inspect.signature(func).parameters

    doc = inspect.getdoc(func)
    param_descriptions: Dict[str, str] = {}
    if doc:
        for line in inspect.cleandoc(doc).splitlines():
            line = line.strip()
            if line.startswith(":param"):
                try:
                    _, rest = line.split(" ", 1)
                    name, desc = rest.split(":", 1)
                    param_descriptions[name.strip()] = desc.strip()
                except ValueError:
                    continue

    # Skip 'self' (for cogs) and 'ctx' (context) parameters
    param_iter = iter(params.values())
    first_param = next(param_iter, None)

    # Heuristic: if the function is bound to a class (cog), 'self' might be the first param.
    # A more robust way would be to check if `func` is a method of a Cog instance later.
    # For now, simple name check.
    if first_param and first_param.name == "self":
        first_param = next(param_iter, None)  # Consume 'self', get next

    if first_param and first_param.name == "ctx":  # Consume 'ctx'
        pass  # ctx is handled, now iterate over actual command options
    elif (
        first_param
    ):  # If first_param was not 'self' and not 'ctx', it's a command option
        param_iter = iter(params.values())  # Reset iterator to include the first param

    for param in param_iter:
        if param.name == "self" or param.name == "ctx":  # Should have been skipped
            continue

        if param.kind == param.VAR_POSITIONAL or param.kind == param.VAR_KEYWORD:
            # *args and **kwargs are not directly supported by slash command options structure.
            # Could raise an error or ignore. For now, ignore.
            # print(f"Warning: *args/**kwargs ({param.name}) are not supported for slash command options.")
            continue

        option_name = param.name
        option_description = param_descriptions.get(
            option_name, f"Description for {option_name}"
        )
        meta = option_meta.get(option_name) if option_meta else None

        param_type_hint = param.annotation
        if param_type_hint == inspect.Parameter.empty:
            # Default to string if no type hint, or raise error.
            # Forcing type hints is generally better for slash commands.
            # raise TypeError(f"Option '{option_name}' must have a type hint for slash commands.")
            param_type_hint = str  # Defaulting to string, can be made stricter

        option_type: Optional[ApplicationCommandOptionType] = None
        choices: Optional[List[ApplicationCommandOptionChoice]] = None

        origin = get_origin(param_type_hint)
        args = get_args(param_type_hint)

        if origin is Annotated:
            param_type_hint = args[0]
            for extra in args[1:]:
                if isinstance(extra, OptionMetadata):
                    meta = extra
            origin = get_origin(param_type_hint)
            args = get_args(param_type_hint)

        actual_type_for_mapping = param_type_hint
        is_optional = False

        if origin is Union:  # Handles Optional[T] which is Union[T, NoneType]
            # Filter out NoneType to get the actual type for mapping
            union_types = [t for t in args if t is not type(None)]
            if len(union_types) == 1:
                actual_type_for_mapping = union_types[0]
                is_optional = True
            else:
                # More complex Unions are not directly supported by a single option type.
                # Could default to STRING or raise.
                # For now, let's assume simple Optional[T] or direct types.
                # print(f"Warning: Complex Union type for '{option_name}' not fully supported, defaulting to STRING.")
                actual_type_for_mapping = str

        elif origin is list and len(args) == 1:
            # List[T] is not a direct option type. Discord handles multiple values for some types
            # via repeated options or specific component interactions, not directly in slash command options.
            # This might indicate a need for a different interaction pattern or custom parsing.
            # For now, treat List[str] as a string, others might error or default.
            # print(f"Warning: List type for '{option_name}' not directly supported as a single option. Consider type {args[0]}.")
            actual_type_for_mapping = args[
                0
            ]  # Use the inner type for mapping, but this is a simplification.

        if origin is Literal:  # typing.Literal['a', 'b']
            choices = []
            for choice_val in args:
                if not isinstance(choice_val, (str, int, float)):
                    raise TypeError(
                        f"Literal choices for '{option_name}' must be str, int, or float. Got {type(choice_val)}."
                    )
                choices.append(
                    ApplicationCommandOptionChoice(
                        data={"name": str(choice_val), "value": choice_val}
                    )
                )
            # The type of the Literal's arguments determines the option type
            if choices:
                literal_arg_type = type(choices[0].value)
                option_type = _type_mapping.get(literal_arg_type)
                if (
                    not option_type and literal_arg_type is float
                ):  # float maps to NUMBER
                    option_type = ApplicationCommandOptionType.NUMBER

        if not option_type:  # If not determined by Literal
            option_type = _type_mapping.get(actual_type_for_mapping)
            # Special handling for User, Member, Role, Attachment, Channel if not directly in _type_mapping
            # This is a bit crude; a proper registry or isinstance checks would be better.
            if not option_type:
                if (
                    actual_type_for_mapping.__name__ == "User"
                    or actual_type_for_mapping.__name__ == "Member"
                ):
                    option_type = ApplicationCommandOptionType.USER
                elif actual_type_for_mapping.__name__ == "Role":
                    option_type = ApplicationCommandOptionType.ROLE
                elif actual_type_for_mapping.__name__ == "Attachment":
                    option_type = ApplicationCommandOptionType.ATTACHMENT
                elif (
                    inspect.isclass(actual_type_for_mapping)
                    and isinstance(Channel, type)
                    and issubclass(actual_type_for_mapping, cast(type, Channel))
                ):
                    option_type = ApplicationCommandOptionType.CHANNEL

        if not option_type:
            # Fallback or error if type couldn't be mapped
            # print(f"Warning: Could not map type '{actual_type_for_mapping}' for option '{option_name}'. Defaulting to STRING.")
            option_type = ApplicationCommandOptionType.STRING  # Default fallback

        required = (param.default == inspect.Parameter.empty) and not is_optional

        data: Dict[str, Any] = {
            "name": option_name,
            "description": option_description,
            "type": option_type.value,
            "required": required,
            "choices": ([c.to_dict() for c in choices] if choices else None),
        }

        if meta:
            if meta.channel_types is not None:
                data["channel_types"] = meta.channel_types
            if meta.min_value is not None:
                data["min_value"] = meta.min_value
            if meta.max_value is not None:
                data["max_value"] = meta.max_value
            if meta.min_length is not None:
                data["min_length"] = meta.min_length
            if meta.max_length is not None:
                data["max_length"] = meta.max_length
            if meta.autocomplete:
                data["autocomplete"] = True

        options.append(ApplicationCommandOption(data=data))
    return options


def _app_command_decorator(
    cls: Type[AppCmdType],
    option_meta: Optional[Dict[str, OptionMetadata]] = None,
    **attrs: Any,
) -> Callable[[Callable[..., Any]], AppCmdType]:
    """Generic factory for creating app command decorators."""

    def decorator(func: Callable[..., Any]) -> AppCmdType:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(
                "Application command callback must be a coroutine function."
            )

        name = attrs.pop("name", None) or func.__name__
        description = attrs.pop("description", None) or inspect.getdoc(func)
        if description:  # Clean up docstring
            description = inspect.cleandoc(description).split("\n\n", 1)[
                0
            ]  # Use first paragraph

        parent_group = attrs.pop("parent", None)
        if parent_group and not isinstance(parent_group, AppCommandGroup):
            raise TypeError(
                "The 'parent' argument must be an AppCommandGroup instance."
            )

        # For User/Message commands, description should be empty for payload, but can be stored for help.
        if cls is UserCommand or cls is MessageCommand:
            actual_description_for_payload = ""
        else:
            actual_description_for_payload = description
            if not actual_description_for_payload and cls is SlashCommand:
                raise ValueError(f"Slash command '{name}' must have a description.")

        # Create the command instance
        cmd_instance = cls(
            callback=func,
            name=name,
            description=actual_description_for_payload,  # Use payload-appropriate description
            **attrs,  # Remaining attributes like guild_ids, nsfw, etc.
        )

        # Store original description if different (e.g. for User/Message commands for help text)
        if description != actual_description_for_payload:
            cmd_instance._full_description = (
                description  # Custom attribute for library use
            )

        if isinstance(cmd_instance, SlashCommand):
            cmd_instance.options = _extract_options_from_signature(func, option_meta)

        if parent_group:
            parent_group.add_command(cmd_instance)  # This also sets cmd_instance.parent

        # Attach command object to the function for later collection by Cog or Client
        # This is a common pattern.
        if hasattr(func, "__app_command_object__"):
            # Function might already be decorated (e.g. hybrid or stacked decorators)
            # Decide on behavior: error, overwrite, or store list of commands.
            # For now, let's assume one app command decorator of a specific type per function.
            # Hybrid commands will need special handling.
            print(
                f"Warning: Function {func.__name__} is already an app command or has one attached. Overwriting."
            )

        setattr(func, "__app_command_object__", cmd_instance)
        setattr(cmd_instance, "__app_command_object__", cmd_instance)

        # If the command is a HybridCommand, also set the attribute
        # that the prefix command system's Cog._inject looks for.
        if isinstance(cmd_instance, HybridCommand):
            setattr(func, "__command_object__", cmd_instance)
            setattr(cmd_instance, "__command_object__", cmd_instance)

        return cmd_instance  # Return the command instance itself, not the function
        # This allows it to be added to cogs/handlers directly.

    return decorator


def slash_command(
    name: Optional[str] = None,
    description: Optional[str] = None,
    guild_ids: Optional[List[Snowflake]] = None,
    default_member_permissions: Optional[str] = None,
    nsfw: bool = False,
    name_localizations: Optional[Dict[str, str]] = None,
    description_localizations: Optional[Dict[str, str]] = None,
    integration_types: Optional[List[IntegrationType]] = None,
    contexts: Optional[List[InteractionContextType]] = None,
    *,
    guilds: bool = True,
    dms: bool = True,
    private_channels: bool = True,
    parent: Optional[AppCommandGroup] = None,  # Added parent parameter
    locale: Optional[str] = None,
    option_meta: Optional[Dict[str, OptionMetadata]] = None,
) -> Callable[[Callable[..., Any]], SlashCommand]:
    """
    Decorator to create a CHAT_INPUT (slash) command.
    Options are inferred from the function's type hints.
    """
    if contexts is None:
        ctxs: List[InteractionContextType] = []
        if guilds:
            ctxs.append(InteractionContextType.GUILD)
        if dms:
            ctxs.append(InteractionContextType.BOT_DM)
        if private_channels:
            ctxs.append(InteractionContextType.PRIVATE_CHANNEL)
        if len(ctxs) != 3:
            contexts = ctxs
    attrs = {
        "name": name,
        "description": description,
        "guild_ids": guild_ids,
        "default_member_permissions": default_member_permissions,
        "nsfw": nsfw,
        "name_localizations": name_localizations,
        "description_localizations": description_localizations,
        "integration_types": integration_types,
        "contexts": contexts,
        "parent": parent,  # Pass parent to attrs
        "locale": locale,
    }
    # Filter out None values to avoid passing them as explicit None to command constructor
    # Keep 'parent' even if None, as _app_command_decorator handles None parent.
    # nsfw default is False, so it's fine if not present and defaults.
    attrs = {k: v for k, v in attrs.items() if v is not None or k in ["nsfw", "parent"]}
    return _app_command_decorator(SlashCommand, option_meta, **attrs)


def user_command(
    name: Optional[str] = None,
    guild_ids: Optional[List[Snowflake]] = None,
    default_member_permissions: Optional[str] = None,
    nsfw: bool = False,  # Though less common for user commands
    name_localizations: Optional[Dict[str, str]] = None,
    integration_types: Optional[List[IntegrationType]] = None,
    contexts: Optional[List[InteractionContextType]] = None,
    locale: Optional[str] = None,
    # description is not used by Discord for User commands
) -> Callable[[Callable[..., Any]], UserCommand]:
    """Decorator to create a USER context menu command."""
    attrs = {
        "name": name,
        "guild_ids": guild_ids,
        "default_member_permissions": default_member_permissions,
        "nsfw": nsfw,
        "name_localizations": name_localizations,
        "integration_types": integration_types,
        "contexts": contexts,
        "locale": locale,
    }
    attrs = {k: v for k, v in attrs.items() if v is not None or k in ["nsfw"]}
    return _app_command_decorator(UserCommand, **attrs)


def message_command(
    name: Optional[str] = None,
    guild_ids: Optional[List[Snowflake]] = None,
    default_member_permissions: Optional[str] = None,
    nsfw: bool = False,  # Though less common for message commands
    name_localizations: Optional[Dict[str, str]] = None,
    integration_types: Optional[List[IntegrationType]] = None,
    contexts: Optional[List[InteractionContextType]] = None,
    locale: Optional[str] = None,
    # description is not used by Discord for Message commands
) -> Callable[[Callable[..., Any]], MessageCommand]:
    """Decorator to create a MESSAGE context menu command."""
    attrs = {
        "name": name,
        "guild_ids": guild_ids,
        "default_member_permissions": default_member_permissions,
        "nsfw": nsfw,
        "name_localizations": name_localizations,
        "integration_types": integration_types,
        "contexts": contexts,
        "locale": locale,
    }
    attrs = {k: v for k, v in attrs.items() if v is not None or k in ["nsfw"]}
    return _app_command_decorator(MessageCommand, **attrs)


def hybrid_command(
    name: Optional[str] = None,
    description: Optional[str] = None,
    guild_ids: Optional[List[Snowflake]] = None,
    default_member_permissions: Optional[str] = None,
    nsfw: bool = False,
    name_localizations: Optional[Dict[str, str]] = None,
    description_localizations: Optional[Dict[str, str]] = None,
    integration_types: Optional[List[IntegrationType]] = None,
    contexts: Optional[List[InteractionContextType]] = None,
    *,
    guilds: bool = True,
    dms: bool = True,
    private_channels: bool = True,
    aliases: Optional[List[str]] = None,  # Specific to prefix command aspect
    # Other prefix-specific options can be added here (e.g., help, brief)
    option_meta: Optional[Dict[str, OptionMetadata]] = None,
    locale: Optional[str] = None,
) -> Callable[[Callable[..., Any]], HybridCommand]:
    """
    Decorator to create a command that can be invoked as both a slash command
    and a traditional prefix-based command.
    Options for the slash command part are inferred from the function's type hints.
    """
    if contexts is None:
        ctxs: List[InteractionContextType] = []
        if guilds:
            ctxs.append(InteractionContextType.GUILD)
        if dms:
            ctxs.append(InteractionContextType.BOT_DM)
        if private_channels:
            ctxs.append(InteractionContextType.PRIVATE_CHANNEL)
        if len(ctxs) != 3:
            contexts = ctxs
    attrs = {
        "name": name,
        "description": description,
        "guild_ids": guild_ids,
        "default_member_permissions": default_member_permissions,
        "nsfw": nsfw,
        "name_localizations": name_localizations,
        "description_localizations": description_localizations,
        "integration_types": integration_types,
        "contexts": contexts,
        "aliases": aliases or [],  # Ensure aliases is a list
        "locale": locale,
    }
    # Filter out None values to avoid passing them as explicit None to command constructor
    # Keep 'nsfw' and 'aliases' as they have defaults (False, [])
    attrs = {
        k: v for k, v in attrs.items() if v is not None or k in ["nsfw", "aliases"]
    }
    return _app_command_decorator(HybridCommand, option_meta, **attrs)


def subcommand(
    parent: AppCommandGroup, *d_args: Any, **d_kwargs: Any
) -> Callable[[Callable[..., Any]], SlashCommand]:
    """Create a subcommand under an existing :class:`AppCommandGroup`."""

    d_kwargs.setdefault("parent", parent)
    return slash_command(*d_args, **d_kwargs)


def group(
    name: str,
    description: Optional[str] = None,
    **kwargs: Any,
) -> Callable[[Optional[Callable[..., Any]]], AppCommandGroup]:
    """Decorator to declare a top level :class:`AppCommandGroup`."""

    def decorator(func: Optional[Callable[..., Any]] = None) -> AppCommandGroup:
        grp = AppCommandGroup(
            name=name,
            description=description,
            guild_ids=kwargs.get("guild_ids"),
            parent=kwargs.get("parent"),
            default_member_permissions=kwargs.get("default_member_permissions"),
            nsfw=kwargs.get("nsfw", False),
            name_localizations=kwargs.get("name_localizations"),
            description_localizations=kwargs.get("description_localizations"),
            integration_types=kwargs.get("integration_types"),
            contexts=kwargs.get("contexts"),
        )

        if func is not None:
            setattr(func, "__app_command_object__", grp)
        return grp

    return decorator


def subcommand_group(
    parent: AppCommandGroup,
    name: str,
    description: Optional[str] = None,
    **kwargs: Any,
) -> Callable[[Optional[Callable[..., Any]]], AppCommandGroup]:
    """Create a nested :class:`AppCommandGroup` under ``parent``."""

    return parent.group(
        name=name,
        description=description,
        **kwargs,
    )
