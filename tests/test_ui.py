import asyncio

import pytest
from types import SimpleNamespace

from disagreement.enums import ButtonStyle
from disagreement.models import SelectOption
from disagreement.ui.button import button, Button
from disagreement.ui.select import select, Select
from disagreement.ui.view import View


@pytest.mark.asyncio
async def test_button_decorator_creates_button():
    @button(label="Hi", custom_id="x")
    async def cb(view, inter):
        pass

    assert isinstance(cb, Button)
    assert cb.label == "Hi"
    view = View()
    view.add_item(cb)
    comps = view.to_components_payload()
    assert comps[0]["components"][0]["custom_id"] == "x"


@pytest.mark.asyncio
async def test_button_decorator_requires_coroutine():
    with pytest.raises(TypeError):
        button()(lambda x, y: None)


@pytest.mark.asyncio
async def test_select_decorator_creates_select():
    options = [SelectOption(label="A", value="a")]

    @select(custom_id="sel", options=options)
    async def cb(view, inter):
        pass

    assert isinstance(cb, Select)
    view = View()
    view.add_item(cb)
    payload = view.to_components_payload()[0]["components"][0]
    assert payload["custom_id"] == "sel"


@pytest.mark.asyncio
async def test_view_dispatch_calls_callback(monkeypatch):
    called = {}

    @button(label="B", custom_id="b")
    async def cb(view, inter):
        called["ok"] = True

    view = View()
    view.add_item(cb)

    class DummyInteraction:
        def __init__(self):
            self.data = SimpleNamespace(custom_id="b")

    interaction = DummyInteraction()
    await view._dispatch(interaction)
    assert called.get("ok")
