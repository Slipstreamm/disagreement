import logging
from typing import Optional


def setup_logging(level: int, file: Optional[str] = None) -> None:
    """Configure logging for the library.

    Parameters
    ----------
    level:
        Logging level from the :mod:`logging` module.
    file:
        Optional file path to write logs to. If ``None``, logs are sent to
        standard output.
    """
    handlers: list[logging.Handler] = []
    if file is None:
        handlers.append(logging.StreamHandler())
    else:
        handlers.append(logging.FileHandler(file))

    logging.basicConfig(
        level=level,
        handlers=handlers,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
