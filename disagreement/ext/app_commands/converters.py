# disagreement/ext/app_commands/converters.py

"""
Converters for transforming application command option values.
"""

from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Protocol,
    TypeVar,
    Union,
    TYPE_CHECKING,
)
from disagreement.enums import ApplicationCommandOptionType
from disagreement.errors import (
    AppCommandOptionConversionError,
)  # To be created in disagreement/errors.py

if TYPE_CHECKING:
    from disagreement.interactions import Interaction  # For context if needed
    from disagreement.models import (
        User,
        Member,
        Role,
        Channel,
        Attachment,
    )  # Discord models
    from disagreement.client import Client  # For fetching objects

T = TypeVar("T", covariant=True)


class Converter(Protocol[T]):
    """
    A protocol for classes that can convert an interaction option value to a specific type.
    """

    async def convert(self, interaction: "Interaction", value: Any) -> T:
        """
        Converts the given value to the target type.

        Parameters:
            interaction (Interaction): The interaction context.
            value (Any): The raw value from the interaction option.

        Returns:
            T: The converted value.

        Raises:
            AppCommandOptionConversionError: If conversion fails.
        """
        ...


# Basic Type Converters


class StringConverter(Converter[str]):
    async def convert(self, interaction: "Interaction", value: Any) -> str:
        if not isinstance(value, str):
            raise AppCommandOptionConversionError(
                f"Expected a string, but got {type(value).__name__}: {value}"
            )
        return value


class IntegerConverter(Converter[int]):
    async def convert(self, interaction: "Interaction", value: Any) -> int:
        if not isinstance(value, int):
            try:
                return int(value)
            except (ValueError, TypeError):
                raise AppCommandOptionConversionError(
                    f"Expected an integer, but got {type(value).__name__}: {value}"
                )
        return value


class BooleanConverter(Converter[bool]):
    async def convert(self, interaction: "Interaction", value: Any) -> bool:
        if not isinstance(value, bool):
            if isinstance(value, str):
                if value.lower() == "true":
                    return True
                elif value.lower() == "false":
                    return False
            raise AppCommandOptionConversionError(
                f"Expected a boolean, but got {type(value).__name__}: {value}"
            )
        return value


class NumberConverter(Converter[float]):  # Discord 'NUMBER' type is float
    async def convert(self, interaction: "Interaction", value: Any) -> float:
        if not isinstance(value, (int, float)):
            try:
                return float(value)
            except (ValueError, TypeError):
                raise AppCommandOptionConversionError(
                    f"Expected a number (float), but got {type(value).__name__}: {value}"
                )
        return float(value)  # Ensure it's a float even if int is passed


# Discord Model Converters


class UserConverter(Converter["User"]):
    def __init__(self, client: "Client"):
        self._client = client

    async def convert(self, interaction: "Interaction", value: Any) -> "User":
        if isinstance(value, str):  # Assume it's a user ID
            user_id = value
            # Attempt to get from interaction resolved data first
            if (
                interaction.data
                and interaction.data.resolved
                and interaction.data.resolved.users
            ):
                user_object = interaction.data.resolved.users.get(
                    user_id
                )  # This is already a User object
                if user_object:
                    return user_object  # Return the already parsed User object

            # Fallback to fetching if not in resolved or if interaction has no resolved data
            try:
                user = await self._client.fetch_user(
                    user_id
                )  # fetch_user now also parses and caches
                if user:
                    return user
                raise AppCommandOptionConversionError(
                    f"User with ID '{user_id}' not found.",
                    option_name="user",
                    original_value=value,
                )
            except Exception as e:  # Catch potential HTTP errors from fetch_user
                raise AppCommandOptionConversionError(
                    f"Failed to fetch user '{user_id}': {e}",
                    option_name="user",
                    original_value=value,
                )
        elif (
            isinstance(value, dict) and "id" in value
        ):  # If it's raw user data dict (less common path now)
            return self._client.parse_user(value)  # parse_user handles dict -> User
        raise AppCommandOptionConversionError(
            f"Expected a user ID string or user data dict, got {type(value).__name__}",
            option_name="user",
            original_value=value,
        )


class MemberConverter(Converter["Member"]):
    def __init__(self, client: "Client"):
        self._client = client

    async def convert(self, interaction: "Interaction", value: Any) -> "Member":
        if not interaction.guild_id:
            raise AppCommandOptionConversionError(
                "Cannot convert to Member outside of a guild context.",
                option_name="member",
            )

        if isinstance(value, str):  # Assume it's a user ID
            member_id = value
            # Attempt to get from interaction resolved data first
            if (
                interaction.data
                and interaction.data.resolved
                and interaction.data.resolved.members
            ):
                # The Member object from resolved.members should already be correctly initialized
                # by ResolvedData, including its User part.
                member = interaction.data.resolved.members.get(member_id)
                if member:
                    return (
                        member  # Return the already resolved and parsed Member object
                    )

            # Fallback to fetching if not in resolved
            try:
                member = await self._client.fetch_member(
                    interaction.guild_id, member_id
                )
                if member:
                    return member
                raise AppCommandOptionConversionError(
                    f"Member with ID '{member_id}' not found in guild '{interaction.guild_id}'.",
                    option_name="member",
                    original_value=value,
                )
            except Exception as e:
                raise AppCommandOptionConversionError(
                    f"Failed to fetch member '{member_id}': {e}",
                    option_name="member",
                    original_value=value,
                )
        elif isinstance(value, dict) and "id" in value.get(
            "user", {}
        ):  # If it's already a member data dict
            return self._client.parse_member(value, interaction.guild_id)
        raise AppCommandOptionConversionError(
            f"Expected a member ID string or member data dict, got {type(value).__name__}",
            option_name="member",
            original_value=value,
        )


class RoleConverter(Converter["Role"]):
    def __init__(self, client: "Client"):
        self._client = client

    async def convert(self, interaction: "Interaction", value: Any) -> "Role":
        if not interaction.guild_id:
            raise AppCommandOptionConversionError(
                "Cannot convert to Role outside of a guild context.", option_name="role"
            )

        if isinstance(value, str):  # Assume it's a role ID
            role_id = value
            # Attempt to get from interaction resolved data first
            if (
                interaction.data
                and interaction.data.resolved
                and interaction.data.resolved.roles
            ):
                role_object = interaction.data.resolved.roles.get(
                    role_id
                )  # Should be a Role object
                if role_object:
                    return role_object

            # Fallback to fetching from guild if not in resolved
            # This requires Client to have a fetch_role method or similar
            try:
                # Assuming Client.fetch_role(guild_id, role_id) will be implemented
                role = await self._client.fetch_role(interaction.guild_id, role_id)
                if role:
                    return role
                raise AppCommandOptionConversionError(
                    f"Role with ID '{role_id}' not found in guild '{interaction.guild_id}'.",
                    option_name="role",
                    original_value=value,
                )
            except Exception as e:
                raise AppCommandOptionConversionError(
                    f"Failed to fetch role '{role_id}': {e}",
                    option_name="role",
                    original_value=value,
                )
        elif (
            isinstance(value, dict) and "id" in value
        ):  # If it's already role data dict
            if (
                not interaction.guild_id
            ):  # Should have been caught earlier, but as a safeguard
                raise AppCommandOptionConversionError(
                    "Guild context is required to parse role data.",
                    option_name="role",
                    original_value=value,
                )
            return self._client.parse_role(value, interaction.guild_id)
        # This path is reached if value is not a string (role ID) and not a dict (role data)
        # or if it's a string but all fetching/lookup attempts failed.
        # The final raise AppCommandOptionConversionError should be outside the if/elif for string values.
        # If value was a string, an error should have been raised within the 'if isinstance(value, str)' block.
        # If it wasn't a string or dict, this is the correct place to raise.
        # The previous structure was slightly off, as the final raise was inside the string check block.
        # Let's ensure the final raise is at the correct scope.
        # The current structure seems to imply that if it's not a string, it must be a dict or error.
        # If it's a string and all lookups fail, an error is raised within that block.
        # If it's a dict and parsing fails (or guild_id missing), error raised.
        # If it's neither, this final raise is correct.
        # The "Function with declared return type "Role" must return value on all code paths"
        # error suggests a path where no return or raise happens.
        # This happens if `isinstance(value, str)` is true, but then all internal paths
        # (resolved check, fetch try/except) don't lead to a return or raise *before*
        # falling out of the `if isinstance(value, str)` block.
        # The `raise AppCommandOptionConversionError` at the end of the `if isinstance(value, str)` block
        # (line 156 in previous version) handles the case where a role ID is given but not found.
        # The one at the very end (line 164 in previous) handles cases where value is not str/dict.

        # Corrected structure for the final raise:
        # It should be at the same level as the initial `if isinstance(value, str):`
        # to catch cases where `value` is neither a str nor a dict.
        # However, the current logic within the `if isinstance(value, str):` block
        # ensures a raise if the role ID is not found.
        # The `elif isinstance(value, dict)` handles the dict case.
        # The final `raise` (line 164) is for types other than str or dict.
        # The Pylance error "Function with declared return type "Role" must return value on all code paths"
        # implies that if `value` is a string, and `interaction.data.resolved.roles.get(role_id)` is None,
        # AND `self._client.fetch_role` returns None (which it can), then the
        # `raise AppCommandOptionConversionError` on line 156 is correctly hit.
        # The issue might be that Pylance doesn't see `AppCommandOptionConversionError` as definitively terminating.
        # This is unlikely. Let's re-verify the logic flow.

        # The `raise` on line 156 is correct if role_id is not found after fetching.
        # The `raise` on line 164 is for when `value` is not a str and not a dict.
        # This seems logically sound. The Pylance error might be a misinterpretation or a subtle issue.
        # For now, the duplicated `except` is the primary syntax error.
        # The "must return value on all code paths" often occurs if an if/elif chain doesn't
        # exhaust all possibilities or if a path through a try/except doesn't guarantee a return/raise.
        # In this case, if `value` is a string, it either returns a Role or raises an error.
        # If `value` is a dict, it either returns a Role or raises an error.
        # If `value` is neither, it raises an error. All paths seem covered.
        # The syntax error from the duplicated `except` is the most likely culprit for Pylance's confusion.
        raise AppCommandOptionConversionError(
            f"Expected a role ID string or role data dict, got {type(value).__name__}",
            option_name="role",
            original_value=value,
        )


class ChannelConverter(Converter["Channel"]):
    def __init__(self, client: "Client"):
        self._client = client

    async def convert(self, interaction: "Interaction", value: Any) -> "Channel":
        if isinstance(value, str):  # Assume it's a channel ID
            channel_id = value
            # Attempt to get from interaction resolved data first
            if (
                interaction.data
                and interaction.data.resolved
                and interaction.data.resolved.channels
            ):
                # Resolved channels are PartialChannel. Client.fetch_channel will get the full typed one.
                partial_channel = interaction.data.resolved.channels.get(channel_id)
                if partial_channel:
                    # Client.fetch_channel should handle fetching and parsing to the correct Channel subtype
                    full_channel = await self._client.fetch_channel(partial_channel.id)
                    if full_channel:
                        return full_channel
                    # If fetch_channel returns None even with a resolved ID, it's an issue.
                    raise AppCommandOptionConversionError(
                        f"Failed to fetch full channel for resolved ID '{channel_id}'.",
                        option_name="channel",
                        original_value=value,
                    )

            # Fallback to fetching directly if not in resolved or if resolved fetch failed
            try:
                channel = await self._client.fetch_channel(
                    channel_id
                )  # fetch_channel handles parsing
                if channel:
                    return channel
                raise AppCommandOptionConversionError(
                    f"Channel with ID '{channel_id}' not found.",
                    option_name="channel",
                    original_value=value,
                )
            except Exception as e:
                raise AppCommandOptionConversionError(
                    f"Failed to fetch channel '{channel_id}': {e}",
                    option_name="channel",
                    original_value=value,
                )
        # Raw channel data dicts are not typically provided for slash command options.
        raise AppCommandOptionConversionError(
            f"Expected a channel ID string, got {type(value).__name__}",
            option_name="channel",
            original_value=value,
        )


class AttachmentConverter(Converter["Attachment"]):
    def __init__(
        self, client: "Client"
    ):  # Client might be needed for future enhancements or consistency
        self._client = client

    async def convert(self, interaction: "Interaction", value: Any) -> "Attachment":
        if isinstance(value, str):  # Value is the attachment ID
            attachment_id = value
            if (
                interaction.data
                and interaction.data.resolved
                and interaction.data.resolved.attachments
            ):
                attachment_object = interaction.data.resolved.attachments.get(
                    attachment_id
                )  # This is already an Attachment object
                if attachment_object:
                    return (
                        attachment_object  # Return the already parsed Attachment object
                    )
            raise AppCommandOptionConversionError(
                f"Attachment with ID '{attachment_id}' not found in resolved data.",
                option_name="attachment",
                original_value=value,
            )
        raise AppCommandOptionConversionError(
            f"Expected an attachment ID string, got {type(value).__name__}",
            option_name="attachment",
            original_value=value,
        )


# Converters can be registered dynamically using
# :meth:`disagreement.ext.app_commands.handler.AppCommandHandler.register_converter`.

# Mapping from ApplicationCommandOptionType to default converters
# This will be used by the AppCommandHandler to automatically apply converters
# if no explicit converter is specified for a command option's type hint.
DEFAULT_CONVERTERS: Dict[
    ApplicationCommandOptionType, Callable[..., Converter[Any]]
] = {  # Changed Callable signature
    ApplicationCommandOptionType.STRING: StringConverter,
    ApplicationCommandOptionType.INTEGER: IntegerConverter,
    ApplicationCommandOptionType.BOOLEAN: BooleanConverter,
    ApplicationCommandOptionType.NUMBER: NumberConverter,
    ApplicationCommandOptionType.USER: UserConverter,
    ApplicationCommandOptionType.CHANNEL: ChannelConverter,
    ApplicationCommandOptionType.ROLE: RoleConverter,
    # ApplicationCommandOptionType.MENTIONABLE: MentionableConverter, # Special case, can be User or Role
    ApplicationCommandOptionType.ATTACHMENT: AttachmentConverter,  # Added
}


async def run_converters(
    interaction: "Interaction",
    param_type: Any,  # The type hint of the parameter
    option_type: ApplicationCommandOptionType,  # The Discord option type
    value: Any,
    client: "Client",  # Needed for model converters
) -> Any:
    """
    Runs the appropriate converter for a given parameter type and value.
    This function will be more complex, handling custom converters, unions, optionals etc.
    For now, a basic lookup.
    """
    converter_class_factory = DEFAULT_CONVERTERS.get(option_type)
    if converter_class_factory:
        # Check if the factory needs the client instance
        # This is a bit simplistic; a more robust way might involve inspecting __init__ signature
        # or having converters register their needs.
        if option_type in [
            ApplicationCommandOptionType.USER,
            ApplicationCommandOptionType.CHANNEL,  # Anticipating these
            ApplicationCommandOptionType.ROLE,
            ApplicationCommandOptionType.MENTIONABLE,
            ApplicationCommandOptionType.ATTACHMENT,
        ]:
            converter_instance = converter_class_factory(client=client)
        else:
            converter_instance = converter_class_factory()

        return await converter_instance.convert(interaction, value)

    # Fallback for unhandled types or if direct type matching is needed
    if param_type is str and isinstance(value, str):
        return value
    if param_type is int and isinstance(value, int):
        return value
    if param_type is bool and isinstance(value, bool):
        return value
    if param_type is float and isinstance(value, (float, int)):
        return float(value)

    # If no specific converter, and it's not a basic type match, raise error or return raw
    # For now, let's raise if no converter found for a specific option type
    if option_type in DEFAULT_CONVERTERS:  # Should have been handled
        pass  # This path implies a logic error above or missing converter in DEFAULT_CONVERTERS

    # If it's a model type but no converter yet, this will need to be handled
    # e.g. if param_type is User and option_type is ApplicationCommandOptionType.USER

    raise AppCommandOptionConversionError(
        f"No suitable converter found for option type {option_type.name} "
        f"with value '{value}' to target type {param_type.__name__ if hasattr(param_type, '__name__') else param_type}"
    )
