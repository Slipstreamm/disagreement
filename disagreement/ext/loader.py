from __future__ import annotations

from importlib import import_module
import sys
from types import ModuleType
from typing import Dict

__all__ = ["load_extension", "unload_extension", "reload_extension"]

_loaded_extensions: Dict[str, ModuleType] = {}


def load_extension(name: str) -> ModuleType:
    """Load an extension by name.

    The extension module must define a ``setup`` coroutine or function that
    will be called after loading. Any value returned by ``setup`` is ignored.
    """

    if name in _loaded_extensions:
        raise ValueError(f"Extension '{name}' already loaded")

    module = import_module(name)

    if not hasattr(module, "setup"):
        raise ImportError(f"Extension '{name}' does not define a setup function")

    module.setup()
    _loaded_extensions[name] = module
    return module


def unload_extension(name: str) -> None:
    """Unload a previously loaded extension."""

    module = _loaded_extensions.pop(name, None)
    if module is None:
        raise ValueError(f"Extension '{name}' is not loaded")

    if hasattr(module, "teardown"):
        module.teardown()

    sys.modules.pop(name, None)


def reload_extension(name: str) -> ModuleType:
    """Reload an extension by name.

    This is a convenience wrapper around :func:`unload_extension` followed by
    :func:`load_extension`.
    """

    unload_extension(name)
    return load_extension(name)
