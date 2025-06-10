from disagreement.components import component_factory
from disagreement.enums import ComponentType, ButtonStyle


def test_component_factory_button():
    data = {
        "type": ComponentType.BUTTON.value,
        "style": ButtonStyle.PRIMARY.value,
        "label": "Click",
        "custom_id": "x",
    }
    comp = component_factory(data)
    assert comp.to_dict()["label"] == "Click"


def test_component_factory_action_row():
    data = {
        "type": ComponentType.ACTION_ROW.value,
        "components": [
            {
                "type": ComponentType.BUTTON.value,
                "style": ButtonStyle.PRIMARY.value,
                "label": "A",
                "custom_id": "b",
            }
        ],
    }
    row = component_factory(data)
    assert len(row.components) == 1
