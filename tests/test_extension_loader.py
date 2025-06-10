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


def test_reload_extension(monkeypatch):
    called_first = create_dummy_module("reload_ext")
    loader.load_extension("reload_ext")

    called_second = {"setup": False, "teardown": False}
    module_second = types.ModuleType("reload_ext")

    def setup_second():
        called_second["setup"] = True

    def teardown_second():
        called_second["teardown"] = True

    module_second.setup = setup_second
    module_second.teardown = teardown_second

    def import_stub(name):
        assert name == "reload_ext"
        sys.modules[name] = module_second
        return module_second

    monkeypatch.setattr(loader, "import_module", import_stub)

    loader.reload_extension("reload_ext")

    assert called_first["teardown"] is True
    assert called_second["setup"] is True
    assert loader._loaded_extensions["reload_ext"] is module_second

    loader.unload_extension("reload_ext")
    assert called_second["teardown"] is True
