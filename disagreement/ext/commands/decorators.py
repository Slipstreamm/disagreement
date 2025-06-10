# disagreement/ext/commands/decorators.py

import asyncio
import inspect
import time
from typing import Callable, Any, Optional, List, TYPE_CHECKING, Awaitable

if TYPE_CHECKING:
    from .core import Command, CommandContext  # For type hinting return or internal use

    # from .cog import Cog # For Cog specific decorators


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

        from .core import (
            Command,
        )  # Late import to avoid circular dependencies at module load time

        # The actual registration will happen when a Cog is added or if commands are global.
        # For now, this decorator creates a Command instance and attaches it to the function,
        # or returns a Command instance that can be collected.

        cmd_name = name or func.__name__

        # Store command attributes on the function itself for later collection by Cog or Client
        # This is a common pattern.
        if hasattr(func, "__command_attrs__"):
            # This case might occur if decorators are stacked in an unusual way,
            # or if a function is decorated multiple times (which should be disallowed or handled).
            # For now, let's assume one @command decorator per function.
            raise TypeError("Function is already a command or has command attributes.")

        # Create the command object. It will be registered by the Cog or Client.
        cmd = Command(callback=func, name=cmd_name, aliases=aliases or [], **attrs)

        # We can attach the command object to the function, so Cogs can find it.
        func.__command_object__ = cmd  # type: ignore # type: ignore[attr-defined]
        return func  # Return the original function, now marked.
        # Or return `cmd` if commands are registered globally immediately.
        # For Cogs, returning `func` and letting Cog collect is cleaner.

    return decorator


def listener(
    name: Optional[str] = None,
) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
    """
    A decorator that marks a function as an event listener within a Cog.
    The actual registration happens when the Cog is added to the client.

    Args:
        name (Optional[str]): The name of the event to listen to.
                              Defaults to the function name (e.g., `on_message`).
    """

    def decorator(
        func: Callable[..., Awaitable[None]],
    ) -> Callable[..., Awaitable[None]]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Listener callback must be a coroutine function.")

        # 'name' here is from the outer 'listener' scope (closure)
        actual_event_name = name or func.__name__
        # Store listener info on the function for Cog to collect
        setattr(func, "__listener_name__", actual_event_name)
        return func

    return decorator  # This must be correctly indented under 'listener'


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
