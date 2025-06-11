# disagreement/ext/commands/decorators.py
from __future__ import annotations

import asyncio
import inspect
import time
from typing import Callable, Any, Optional, List, TYPE_CHECKING, Awaitable

if TYPE_CHECKING:
    from .core import Command, CommandContext
    from disagreement.permissions import Permissions
    from disagreement.models import Member, Guild, Channel


def command(
    name: Optional[str] = None, aliases: Optional[List[str]] = None, **attrs: Any
) -> Callable:
    """
    A decorator that transforms a function into a Command.

    Args:
        name (Optional[str]): The name of the command. Defaults to the function name.
        aliases (Optional[List[str]]): Alternative names for the command.
        **attrs: Additional attributes to pass to the Command constructor
                 (e.g., brief, description, hidden).

    Returns:
        Callable: A decorator that registers the command.
    """

    def decorator(
        func: Callable[..., Awaitable[None]],
    ) -> Callable[..., Awaitable[None]]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Command callback must be a coroutine function.")

        from .core import Command

        cmd_name = name or func.__name__

        if hasattr(func, "__command_attrs__"):
            raise TypeError("Function is already a command or has command attributes.")

        cmd = Command(callback=func, name=cmd_name, aliases=aliases or [], **attrs)
        func.__command_object__ = cmd  # type: ignore
        return func

    return decorator


def listener(
    name: Optional[str] = None,
) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
    """
    A decorator that marks a function as an event listener within a Cog.
    """

    def decorator(
        func: Callable[..., Awaitable[None]],
    ) -> Callable[..., Awaitable[None]]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Listener callback must be a coroutine function.")

        actual_event_name = name or func.__name__
        setattr(func, "__listener_name__", actual_event_name)
        return func

    return decorator


def check(
    predicate: Callable[["CommandContext"], Awaitable[bool] | bool],
) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
    """Decorator to add a check to a command."""

    def decorator(
        func: Callable[..., Awaitable[None]],
    ) -> Callable[..., Awaitable[None]]:
        checks = getattr(func, "__command_checks__", [])
        checks.append(predicate)
        setattr(func, "__command_checks__", checks)
        return func

    return decorator


def check_any(
    *predicates: Callable[["CommandContext"], Awaitable[bool] | bool]
) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
    """Decorator that passes if any predicate returns ``True``."""

    async def predicate(ctx: "CommandContext") -> bool:
        from .errors import CheckAnyFailure, CheckFailure

        errors = []
        for p in predicates:
            try:
                result = p(ctx)
                if inspect.isawaitable(result):
                    result = await result
                if result:
                    return True
            except CheckFailure as e:
                errors.append(e)
        raise CheckAnyFailure(errors)

    return check(predicate)


def max_concurrency(
    number: int, per: str = "user"
) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
    """Limit how many concurrent invocations of a command are allowed.

    Parameters
    ----------
    number:
        The maximum number of concurrent invocations.
    per:
        The scope of the limiter. Can be ``"user"``, ``"guild"`` or ``"global"``.
    """

    if number < 1:
        raise ValueError("Concurrency number must be at least 1.")
    if per not in {"user", "guild", "global"}:
        raise ValueError("per must be 'user', 'guild', or 'global'.")

    def decorator(
        func: Callable[..., Awaitable[None]],
    ) -> Callable[..., Awaitable[None]]:
        setattr(func, "__max_concurrency__", (number, per))
        return func

    return decorator


def cooldown(
    rate: int, per: float
) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
    """Simple per-user cooldown decorator."""

    buckets: dict[str, dict[str, float]] = {}

    async def predicate(ctx: "CommandContext") -> bool:
        from .errors import CommandOnCooldown

        now = time.monotonic()
        user_buckets = buckets.setdefault(ctx.command.name, {})
        reset = user_buckets.get(ctx.author.id, 0)
        if now < reset:
            raise CommandOnCooldown(reset - now)
        user_buckets[ctx.author.id] = now + per
        return True

    return check(predicate)


def _compute_permissions(
    member: "Member", channel: "Channel", guild: "Guild"
) -> "Permissions":
    """Compute the effective permissions for a member in a channel."""
    return channel.permissions_for(member)


def requires_permissions(
    *perms: "Permissions",
) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
    """Check that the invoking member has the given permissions in the channel."""

    async def predicate(ctx: "CommandContext") -> bool:
        from .errors import CheckFailure
        from disagreement.permissions import (
            has_permissions,
            missing_permissions,
        )
        from disagreement.models import Member

        channel = getattr(ctx, "channel", None)
        if channel is None and hasattr(ctx.bot, "get_channel"):
            channel = ctx.bot.get_channel(ctx.message.channel_id)
        if channel is None and hasattr(ctx.bot, "fetch_channel"):
            channel = await ctx.bot.fetch_channel(ctx.message.channel_id)

        if channel is None:
            raise CheckFailure("Channel for permission check not found.")

        guild = getattr(channel, "guild", None)
        if not guild and hasattr(channel, "guild_id") and channel.guild_id:
            if hasattr(ctx.bot, "get_guild"):
                guild = ctx.bot.get_guild(channel.guild_id)
            if not guild and hasattr(ctx.bot, "fetch_guild"):
                guild = await ctx.bot.fetch_guild(channel.guild_id)

        if not guild:
            is_dm = not hasattr(channel, "guild_id") or not channel.guild_id
            if is_dm:
                if perms:
                    raise CheckFailure("Permission checks are not supported in DMs.")
                return True
            raise CheckFailure("Guild for permission check not found.")

        member = ctx.author
        if not isinstance(member, Member):
            member = guild.get_member(ctx.author.id)
            if not member and hasattr(ctx.bot, "fetch_member"):
                member = await ctx.bot.fetch_member(guild.id, ctx.author.id)

        if not member:
            raise CheckFailure("Could not resolve author to a guild member.")

        perms_value = _compute_permissions(member, channel, guild)

        if not has_permissions(perms_value, *perms):
            missing = missing_permissions(perms_value, *perms)
            missing_names = ", ".join(p.name for p in missing if p.name)
            raise CheckFailure(f"Missing permissions: {missing_names}")
        return True

    return check(predicate)
