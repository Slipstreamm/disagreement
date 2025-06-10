import sys
import types

import pytest

from disagreement.ext import loader


def create_dummy_module(name):
    mod = types.ModuleType(name)
    called = {"setup": False, "teardown": False}

    def setup():
        called["setup"] = True

    def teardown():
        called["teardown"] = True

    mod.setup = setup
    mod.teardown = teardown
    sys.modules[name] = mod
    return called


def test_load_and_unload_extension():
    called = create_dummy_module("dummy_ext")

    module = loader.load_extension("dummy_ext")
    assert module is sys.modules["dummy_ext"]
    assert called["setup"] is True

    loader.unload_extension("dummy_ext")
    assert called["teardown"] is True
    assert "dummy_ext" not in loader._loaded_extensions
    assert "dummy_ext" not in sys.modules


def test_load_extension_twice_raises():
    called = create_dummy_module("repeat_ext")
    loader.load_extension("repeat_ext")
    with pytest.raises(ValueError):
        loader.load_extension("repeat_ext")
    loader.unload_extension("repeat_ext")
    assert called["teardown"] is True
