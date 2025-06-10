# disagreement/ext/app_commands/commands.py

import inspect
from typing import Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING

from disagreement.enums import (
    ApplicationCommandType,
    ApplicationCommandOptionType,
    IntegrationType,
    InteractionContextType,
)
from disagreement.interactions import ApplicationCommandOption, Snowflake

if TYPE_CHECKING:
    from disagreement.ext.commands.core import Command as PrefixCommand
    from disagreement.ext.commands.cog import Cog

if not TYPE_CHECKING:
    try:
        from disagreement.ext.commands.core import Command as PrefixCommand
    except ImportError:
        PrefixCommand = Any


class AppCommand:
    """
    Base class for an application command.

    Attributes:
        name (str): The name of the command.
        description (Optional[str]): The description of the command.
            Required for CHAT_INPUT, empty for USER and MESSAGE commands.
        callback (Callable[..., Any]): The coroutine function that will be called when the command is executed.
        type (ApplicationCommandType): The type of the application command.
        options (Optional[List[ApplicationCommandOption]]): Parameters for the command. Populated by decorators.
        guild_ids (Optional[List[Snowflake]]): List of guild IDs where this command is active. None for global.
        default_member_permissions (Optional[str]): Bitwise permissions required by default for users to run the command.
        nsfw (bool): Whether the command is age-restricted.
        parent (Optional['AppCommandGroup']): The parent group if this is a subcommand.
        cog (Optional[Cog]): The cog this command belongs to, if any.
        _full_description (Optional[str]): Stores the original full description, e.g. from docstring,
                                          even if the payload description is different (like for User/Message commands).
        name_localizations (Optional[Dict[str, str]]): Localizations for the command's name.
        description_localizations (Optional[Dict[str, str]]): Localizations for the command's description.
        integration_types (Optional[List[IntegrationType]]): Installation contexts.
        contexts (Optional[List[InteractionContextType]]): Interaction contexts.
    """

    def __init__(
        self,
        callback: Callable[..., Any],
        *,
        name: str,
        description: Optional[str] = None,
        locale: Optional[str] = None,
        type: "ApplicationCommandType",
        guild_ids: Optional[List["Snowflake"]] = None,
        default_member_permissions: Optional[str] = None,
        nsfw: bool = False,
        parent: Optional["AppCommandGroup"] = None,
        cog: Optional[
            Any
        ] = None,  # Changed 'Cog' to Any to avoid runtime import issues if Cog is complex
        name_localizations: Optional[Dict[str, str]] = None,
        description_localizations: Optional[Dict[str, str]] = None,
        integration_types: Optional[List["IntegrationType"]] = None,
        contexts: Optional[List["InteractionContextType"]] = None,
    ):
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError(
                "Application command callback must be a coroutine function."
            )

        if locale:
            from disagreement import i18n

            translate = i18n.translate

            self.name = translate(name, locale)
            self.description = (
                translate(description, locale) if description is not None else None
            )
        else:
            self.name = name
            self.description = description
        self.locale: Optional[str] = locale
        self.callback: Callable[..., Any] = callback
        self.type: "ApplicationCommandType" = type
        self.options: List["ApplicationCommandOption"] = []  # Populated by decorator
        self.guild_ids: Optional[List["Snowflake"]] = guild_ids
        self.default_member_permissions: Optional[str] = default_member_permissions
        self.nsfw: bool = nsfw
        self.parent: Optional["AppCommandGroup"] = parent
        self.cog: Optional[Any] = cog  # Changed 'Cog' to Any
        self.name_localizations: Optional[Dict[str, str]] = name_localizations
        self.description_localizations: Optional[Dict[str, str]] = (
            description_localizations
        )
        self.integration_types: Optional[List["IntegrationType"]] = integration_types
        self.contexts: Optional[List["InteractionContextType"]] = contexts
        self._full_description: Optional[str] = (
            None  # Initialized by decorator if needed
        )

        # Signature for argument parsing by decorators/handlers
        self.params = inspect.signature(callback).parameters

    async def invoke(
        self, context: "AppCommandContext", *args: Any, **kwargs: Any
    ) -> None:
        """Invokes the command's callback with the given context and arguments."""
        # Similar to Command.invoke, handle cog if present
        actual_args = []
        if self.cog:
            actual_args.append(self.cog)
        actual_args.append(context)
        actual_args.extend(args)

        await self.callback(*actual_args, **kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the command to a dictionary payload for Discord API."""
        payload: Dict[str, Any] = {
            "name": self.name,
            "type": self.type.value,
            # CHAT_INPUT commands require a description.
            # USER and MESSAGE commands must have an empty description in the payload if not omitted.
            # The constructor for UserCommand/MessageCommand already sets self.description to ""
            "description": (
                self.description
                if self.type == ApplicationCommandType.CHAT_INPUT
                else ""
            ),
        }

        # For CHAT_INPUT commands, options are its parameters.
        # For USER/MESSAGE commands, options should be empty or not present.
        if self.type == ApplicationCommandType.CHAT_INPUT and self.options:
            payload["options"] = [opt.to_dict() for opt in self.options]

        if self.default_member_permissions is not None:  # Can be "0" for no permissions
            payload["default_member_permissions"] = str(self.default_member_permissions)

        # nsfw defaults to False, only include if True
        if self.nsfw:
            payload["nsfw"] = True

        if self.name_localizations:
            payload["name_localizations"] = self.name_localizations

        # Description localizations only apply if there's a description (CHAT_INPUT commands)
        if (
            self.type == ApplicationCommandType.CHAT_INPUT
            and self.description
            and self.description_localizations
        ):
            payload["description_localizations"] = self.description_localizations

        if self.integration_types:
            payload["integration_types"] = [it.value for it in self.integration_types]

        if self.contexts:
            payload["contexts"] = [ict.value for ict in self.contexts]

        # According to Discord API, guild_id is not part of this payload,
        # it's used in the URL path for guild-specific command registration.
        # However, the global command registration takes an 'application_id' in the payload,
        # but that's handled by the HTTPClient.

        return payload

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' type={self.type!r}>"


class SlashCommand(AppCommand):
    """Represents a CHAT_INPUT (slash) command."""

    def __init__(self, callback: Callable[..., Any], **kwargs: Any):
        if not kwargs.get("description"):
            raise ValueError("SlashCommand requires a description.")
        super().__init__(callback, type=ApplicationCommandType.CHAT_INPUT, **kwargs)


class UserCommand(AppCommand):
    """Represents a USER context menu command."""

    def __init__(self, callback: Callable[..., Any], **kwargs: Any):
        # Description is not allowed by Discord API for User Commands, but can be set to empty string.
        kwargs["description"] = kwargs.get(
            "description", ""
        )  # Ensure it's empty or not present in payload
        super().__init__(callback, type=ApplicationCommandType.USER, **kwargs)


class MessageCommand(AppCommand):
    """Represents a MESSAGE context menu command."""

    def __init__(self, callback: Callable[..., Any], **kwargs: Any):
        # Description is not allowed by Discord API for Message Commands.
        kwargs["description"] = kwargs.get("description", "")
        super().__init__(callback, type=ApplicationCommandType.MESSAGE, **kwargs)




class AppCommandGroup:
    """
    Represents a group of application commands (subcommands or subcommand groups).
    This itself is not directly callable but acts as a namespace.
    """

    def __init__(
        self,
        name: str,
        description: Optional[
            str
        ] = None,  # Required for top-level groups that form part of a slash command
        guild_ids: Optional[List["Snowflake"]] = None,
        parent: Optional["AppCommandGroup"] = None,
        default_member_permissions: Optional[str] = None,
        nsfw: bool = False,
        name_localizations: Optional[Dict[str, str]] = None,
        description_localizations: Optional[Dict[str, str]] = None,
        integration_types: Optional[List["IntegrationType"]] = None,
        contexts: Optional[List["InteractionContextType"]] = None,
    ):
        self.name: str = name
        self.description: Optional[str] = description
        self.guild_ids: Optional[List["Snowflake"]] = guild_ids
        self.parent: Optional["AppCommandGroup"] = parent
        self.commands: Dict[str, Union[AppCommand, "AppCommandGroup"]] = {}
        self.default_member_permissions: Optional[str] = default_member_permissions
        self.nsfw: bool = nsfw
        self.name_localizations: Optional[Dict[str, str]] = name_localizations
        self.description_localizations: Optional[Dict[str, str]] = (
            description_localizations
        )
        self.integration_types: Optional[List["IntegrationType"]] = integration_types
        self.contexts: Optional[List["InteractionContextType"]] = contexts
        # A group itself doesn't have a cog directly, its commands do.

    def add_command(self, command: Union[AppCommand, "AppCommandGroup"]) -> None:
        if command.name in self.commands:
            raise ValueError(
                f"Command or group '{command.name}' already exists in group '{self.name}'."
            )
        command.parent = self
        self.commands[command.name] = command

    def get_command(self, name: str) -> Optional[Union[AppCommand, "AppCommandGroup"]]:
        return self.commands.get(name)

    def command(self, *d_args: Any, **d_kwargs: Any):
        d_kwargs.setdefault("parent", self)
        from .decorators import slash_command

        return slash_command(*d_args, **d_kwargs)

    def group(
        self,
        name: str,
        description: Optional[str] = None,
        **kwargs: Any,
    ):
        sub_group = AppCommandGroup(
            name=name,
            description=description,
            parent=self,
            guild_ids=kwargs.get("guild_ids"),
            default_member_permissions=kwargs.get("default_member_permissions"),
            nsfw=kwargs.get("nsfw", False),
            name_localizations=kwargs.get("name_localizations"),
            description_localizations=kwargs.get("description_localizations"),
            integration_types=kwargs.get("integration_types"),
            contexts=kwargs.get("contexts"),
        )
        self.add_command(sub_group)

        def decorator(func: Optional[Callable[..., Any]] = None):
            if func is not None:
                setattr(func, "__app_command_object__", sub_group)
                return sub_group
            return sub_group

        return decorator

    def __repr__(self) -> str:
        return f"<AppCommandGroup name='{self.name}' commands={len(self.commands)}>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the command group to a dictionary payload for Discord API.
        This represents a top-level command that has subcommands/subcommand groups.
        """
        payload: Dict[str, Any] = {
            "name": self.name,
            "type": ApplicationCommandType.CHAT_INPUT.value,  # Groups are implicitly CHAT_INPUT
            "description": self.description
            or "No description provided",  # Top-level groups require a description
            "options": [],
        }

        if self.default_member_permissions is not None:
            payload["default_member_permissions"] = str(self.default_member_permissions)
        if self.nsfw:
            payload["nsfw"] = True
        if self.name_localizations:
            payload["name_localizations"] = self.name_localizations
        if (
            self.description and self.description_localizations
        ):  # Only if description is not empty
            payload["description_localizations"] = self.description_localizations
        if self.integration_types:
            payload["integration_types"] = [it.value for it in self.integration_types]
        if self.contexts:
            payload["contexts"] = [ict.value for ict in self.contexts]

        # guild_ids are handled at the registration level, not in this specific payload part.

        options_payload: List[Dict[str, Any]] = []
        for cmd_name, command_or_group in self.commands.items():
            if isinstance(command_or_group, AppCommand):  # This is a Subcommand
                # Subcommands use their own options (parameters)
                sub_options = (
                    [opt.to_dict() for opt in command_or_group.options]
                    if command_or_group.options
                    else []
                )
                option_dict = {
                    "type": ApplicationCommandOptionType.SUB_COMMAND.value,
                    "name": command_or_group.name,
                    "description": command_or_group.description
                    or "No description provided",
                    "options": sub_options,
                }
                # Add localization for subcommand name and description if available
                if command_or_group.name_localizations:
                    option_dict["name_localizations"] = (
                        command_or_group.name_localizations
                    )
                if (
                    command_or_group.description
                    and command_or_group.description_localizations
                ):
                    option_dict["description_localizations"] = (
                        command_or_group.description_localizations
                    )
                options_payload.append(option_dict)

            elif isinstance(
                command_or_group, AppCommandGroup
            ):  # This is a Subcommand Group
                # Subcommand groups have their subcommands/groups as options
                sub_group_options: List[Dict[str, Any]] = []
                for sub_cmd_name, sub_command in command_or_group.commands.items():
                    # Nested groups can only contain subcommands, not further nested groups as per Discord rules.
                    # So, sub_command here must be an AppCommand.
                    if isinstance(
                        sub_command, AppCommand
                    ):  # Should always be AppCommand if structure is valid
                        sub_cmd_options = (
                            [opt.to_dict() for opt in sub_command.options]
                            if sub_command.options
                            else []
                        )
                        sub_group_option_entry = {
                            "type": ApplicationCommandOptionType.SUB_COMMAND.value,
                            "name": sub_command.name,
                            "description": sub_command.description
                            or "No description provided",
                            "options": sub_cmd_options,
                        }
                        # Add localization for subcommand name and description if available
                        if sub_command.name_localizations:
                            sub_group_option_entry["name_localizations"] = (
                                sub_command.name_localizations
                            )
                        if (
                            sub_command.description
                            and sub_command.description_localizations
                        ):
                            sub_group_option_entry["description_localizations"] = (
                                sub_command.description_localizations
                            )
                        sub_group_options.append(sub_group_option_entry)
                    # else:
                    #     # This case implies a group nested inside a group, which then contains another group.
                    #     # Discord's structure is:
                    #     # command -> option (SUB_COMMAND_GROUP) -> option (SUB_COMMAND) -> option (param)
                    #     # This should be caught by validation logic in decorators or add_command.
                    #     # For now, we assume valid structure where AppCommandGroup's commands are AppCommands.
                    #     pass

                option_dict = {
                    "type": ApplicationCommandOptionType.SUB_COMMAND_GROUP.value,
                    "name": command_or_group.name,
                    "description": command_or_group.description
                    or "No description provided",
                    "options": sub_group_options,  # These are the SUB_COMMANDs
                }
                # Add localization for subcommand group name and description if available
                if command_or_group.name_localizations:
                    option_dict["name_localizations"] = (
                        command_or_group.name_localizations
                    )
                if (
                    command_or_group.description
                    and command_or_group.description_localizations
                ):
                    option_dict["description_localizations"] = (
                        command_or_group.description_localizations
                    )
                options_payload.append(option_dict)

        payload["options"] = options_payload
        return payload


# Need to import asyncio for iscoroutinefunction check
import asyncio

if TYPE_CHECKING:
    from .context import AppCommandContext  # For type hint in AppCommand.invoke

    # Ensure ApplicationCommandOptionType is available for the to_dict method
    from disagreement.enums import ApplicationCommandOptionType
