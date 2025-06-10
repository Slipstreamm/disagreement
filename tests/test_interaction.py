import pytest

from disagreement.models import Embed


@pytest.mark.asyncio
async def test_edit_calls_http_with_payload(dummy_bot, interaction):
    await interaction.edit(content="updated")
    dummy_bot._http.edit_original_interaction_response.assert_called_once()
    kwargs = dummy_bot._http.edit_original_interaction_response.call_args.kwargs
    assert kwargs["application_id"] == dummy_bot.application_id
    assert kwargs["interaction_token"] == interaction.token
    assert kwargs["payload"] == {"content": "updated"}


@pytest.mark.asyncio
async def test_edit_embed_and_embeds_raises(dummy_bot, interaction):
    with pytest.raises(ValueError):
        await interaction.edit(embed=Embed(), embeds=[Embed()])
