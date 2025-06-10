import pytest

from disagreement.interactions import Interaction
from disagreement.ui import Modal, text_input
from disagreement.enums import InteractionCallbackType, TextInputStyle


class MyModal(Modal):
    def __init__(self):
        super().__init__(title="Test", custom_id="m1")

    @text_input(label="Name", style=TextInputStyle.SHORT)
    async def name(self, interaction: Interaction):
        pass


def test_modal_to_dict():
    modal = MyModal()
    data = modal.to_dict()
    assert data["title"] == "Test"
    assert data["custom_id"] == "m1"
    assert data["components"][0]["components"][0]["label"] == "Name"


@pytest.mark.asyncio
async def test_respond_modal(dummy_bot, interaction):
    modal = MyModal()
    await interaction.respond_modal(modal)
    dummy_bot._http.create_interaction_response.assert_called_once()
    payload = dummy_bot._http.create_interaction_response.call_args.kwargs["payload"]
    assert payload["type"] == InteractionCallbackType.MODAL.value
    assert payload["data"]["custom_id"] == "m1"
