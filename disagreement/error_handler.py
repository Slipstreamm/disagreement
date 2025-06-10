import asyncio
import logging
import traceback
from typing import Optional

from .logging_config import setup_logging


def setup_global_error_handler(
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> None:
    """Configure a basic global error handler for the provided loop.

    The handler logs unhandled exceptions so they don't crash the bot.
    """
    if loop is None:
        loop = asyncio.get_event_loop()

    if not logging.getLogger().hasHandlers():
        setup_logging(logging.ERROR)

    def handle_exception(loop: asyncio.AbstractEventLoop, context: dict) -> None:
        exception = context.get("exception")
        if exception:
            logging.error("Unhandled exception in event loop: %s", exception)
            traceback.print_exception(
                type(exception), exception, exception.__traceback__
            )
        else:
            message = context.get("message")
            logging.error("Event loop error: %s", message)

    loop.set_exception_handler(handle_exception)
