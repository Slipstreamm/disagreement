import pytest

from disagreement.ui.view import View
from disagreement.ui.button import Button
from disagreement.ui.select import Select
from disagreement.enums import ButtonStyle, ComponentType
from disagreement.models import SelectOption


def test_basic_layout_keeps_one_item_per_row():
    view = View()
    view.add_item(Button(style=ButtonStyle.PRIMARY, label="a"))
    view.add_item(Button(style=ButtonStyle.PRIMARY, label="b"))

    rows = view.to_components()
    assert len(rows) == 2
    assert all(len(r.components) == 1 for r in rows)


def test_advanced_layout_groups_buttons():
    view = View()
    for i in range(6):
        view.add_item(Button(style=ButtonStyle.PRIMARY, label=str(i)))

    rows = view.layout_components_advanced()
    assert len(rows) == 2
    assert len(rows[0].components) == 5
    assert len(rows[1].components) == 1


def test_advanced_layout_select_separate():
    view = View()
    view.add_item(Select(custom_id="s", options=[SelectOption(label="A", value="a")]))
    view.add_item(Button(style=ButtonStyle.PRIMARY, label="b1"))
    view.add_item(Button(style=ButtonStyle.PRIMARY, label="b2"))

    rows = view.layout_components_advanced()
    assert len(rows) == 2
    assert rows[0].components[0].type == ComponentType.STRING_SELECT
    assert all(c.type == ComponentType.BUTTON for c in rows[1].components)
    assert len(rows[1].components) == 2


def test_advanced_layout_respects_row_attribute():
    view = View()
    view.add_item(Button(style=ButtonStyle.PRIMARY, label="x", row=1))
    view.add_item(Button(style=ButtonStyle.PRIMARY, label="y", row=1))
    view.add_item(Button(style=ButtonStyle.PRIMARY, label="z", row=0))

    rows = view.layout_components_advanced()
    assert len(rows) == 2
    assert len(rows[0].components) == 1
    assert len(rows[1].components) == 2
