import pytest

from disagreement.ui import Modal, TextInput


class MyModal(Modal):
    def __init__(self):
        super().__init__(title="T", custom_id="m")
        self.input = TextInput(label="L", custom_id="i")


@pytest.mark.asyncio
async def test_send_modal(dummy_bot, interaction):
    modal = MyModal()
    await interaction.response.send_modal(modal)
    dummy_bot._http.create_interaction_response.assert_called_once()
