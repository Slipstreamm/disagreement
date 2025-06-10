"""Utility class for working with either command or app contexts."""

from __future__ import annotations

from typing import Any, Union

from .ext.commands.core import CommandContext
from .ext.app_commands.context import AppCommandContext


class HybridContext:
    """Wraps :class:`CommandContext` and :class:`AppCommandContext`.

    Provides a single :meth:`send` method that proxies to ``reply`` for
    prefix commands and to ``send`` for slash commands.
    """

    def __init__(self, ctx: Union[CommandContext, AppCommandContext]):
        self._ctx = ctx

    async def send(self, *args: Any, **kwargs: Any):
        if isinstance(self._ctx, AppCommandContext):
            return await self._ctx.send(*args, **kwargs)
        return await self._ctx.reply(*args, **kwargs)

    async def edit(self, *args: Any, **kwargs: Any):
        if hasattr(self._ctx, "edit"):
            return await self._ctx.edit(*args, **kwargs)
        raise AttributeError("Underlying context does not support editing.")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._ctx, name)
