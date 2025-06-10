# disagreement/ext/commands/converters.py

from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypeVar, Generic
from abc import ABC, abstractmethod
import re

from .errors import BadArgument
from disagreement.models import Member, Guild, Role

if TYPE_CHECKING:
    from .core import CommandContext

T = TypeVar("T")


class Converter(ABC, Generic[T]):
    """
    Base class for custom command argument converters.
    Subclasses must implement the `convert` method.
    """

    async def convert(self, ctx: "CommandContext", argument: str) -> T:
        """
        Converts the argument to the desired type.

        Args:
            ctx: The invocation context.
            argument: The string argument to convert.

        Returns:
            The converted argument.

        Raises:
            BadArgument: If the conversion fails.
        """
        raise NotImplementedError("Converter subclass must implement convert method.")


# --- Built-in Type Converters ---


class IntConverter(Converter[int]):
    async def convert(self, ctx: "CommandContext", argument: str) -> int:
        try:
            return int(argument)
        except ValueError:
            raise BadArgument(f"'{argument}' is not a valid integer.")


class FloatConverter(Converter[float]):
    async def convert(self, ctx: "CommandContext", argument: str) -> float:
        try:
            return float(argument)
        except ValueError:
            raise BadArgument(f"'{argument}' is not a valid number.")


class BoolConverter(Converter[bool]):
    async def convert(self, ctx: "CommandContext", argument: str) -> bool:
        lowered = argument.lower()
        if lowered in ("yes", "y", "true", "t", "1", "on", "enable", "enabled"):
            return True
        elif lowered in ("no", "n", "false", "f", "0", "off", "disable", "disabled"):
            return False
        raise BadArgument(f"'{argument}' is not a valid boolean-like value.")


class StringConverter(Converter[str]):
    async def convert(self, ctx: "CommandContext", argument: str) -> str:
        # For basic string, no conversion is needed, but this provides a consistent interface
        return argument


# --- Discord Model Converters ---


class MemberConverter(Converter["Member"]):
    async def convert(self, ctx: "CommandContext", argument: str) -> "Member":
        if not ctx.message.guild_id:
            raise BadArgument("Member converter requires guild context.")

        match = re.match(r"<@!?(\d+)>$", argument)
        member_id = match.group(1) if match else argument

        guild = ctx.bot.get_guild(ctx.message.guild_id)
        if guild:
            member = guild.get_member(member_id)
            if member:
                return member

        member = await ctx.bot.fetch_member(ctx.message.guild_id, member_id)
        if member:
            return member
        raise BadArgument(f"Member '{argument}' not found.")


class RoleConverter(Converter["Role"]):
    async def convert(self, ctx: "CommandContext", argument: str) -> "Role":
        if not ctx.message.guild_id:
            raise BadArgument("Role converter requires guild context.")

        match = re.match(r"<@&(?P<id>\d+)>$", argument)
        role_id = match.group("id") if match else argument

        guild = ctx.bot.get_guild(ctx.message.guild_id)
        if guild:
            role = guild.get_role(role_id)
            if role:
                return role

        role = await ctx.bot.fetch_role(ctx.message.guild_id, role_id)
        if role:
            return role
        raise BadArgument(f"Role '{argument}' not found.")


class GuildConverter(Converter["Guild"]):
    async def convert(self, ctx: "CommandContext", argument: str) -> "Guild":
        guild_id = argument.strip("<>")  # allow <id> style

        guild = ctx.bot.get_guild(guild_id)
        if guild:
            return guild

        guild = await ctx.bot.fetch_guild(guild_id)
        if guild:
            return guild
        raise BadArgument(f"Guild '{argument}' not found.")


# Default converters mapping
DEFAULT_CONVERTERS: dict[type, Converter[Any]] = {
    int: IntConverter(),
    float: FloatConverter(),
    bool: BoolConverter(),
    str: StringConverter(),
    Member: MemberConverter(),
    Guild: GuildConverter(),
    Role: RoleConverter(),
    # User: UserConverter(), # Add when User model and converter are ready
}


async def run_converters(ctx: "CommandContext", annotation: Any, argument: str) -> Any:
    """
    Attempts to run a converter for the given annotation and argument.
    """
    converter = DEFAULT_CONVERTERS.get(annotation)
    if converter:
        return await converter.convert(ctx, argument)

    # If no direct converter, check if annotation itself is a Converter subclass
    if inspect.isclass(annotation) and issubclass(annotation, Converter):
        try:
            instance = annotation()  # type: ignore
            return await instance.convert(ctx, argument)
        except Exception as e:  # Catch instantiation errors or other issues
            raise BadArgument(
                f"Failed to use custom converter {annotation.__name__}: {e}"
            )

    # If it's a custom class that's not a Converter, we can't handle it by default
    # Or if it's a complex type hint like Union, Optional, Literal etc.
    # This part needs more advanced logic for those.

    # For now, if no specific converter, and it's not 'str', raise error or return as str?
    # Let's be strict for now if an annotation is given but no converter found.
    if annotation is not str and annotation is not inspect.Parameter.empty:
        raise BadArgument(f"No converter found for type annotation '{annotation}'.")

    return argument  # Default to string if no annotation or annotation is str


# Need to import inspect for the run_converters function
import inspect
