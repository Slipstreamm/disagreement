import asyncio
from unittest.mock import AsyncMock

import pytest

from disagreement.ext.app_commands.context import AppCommandContext
from disagreement.interactions import Interaction
from disagreement.enums import InteractionType, MessageFlags
from disagreement.models import (
    Embed,
    ActionRow,
    Button,
    Container,
    TextDisplay,
)
from disagreement.enums import ButtonStyle, ComponentType


class DummyHTTP:
    def __init__(self):
        self.create_interaction_response = AsyncMock()
        self.create_followup_message = AsyncMock(return_value={"id": "123"})
        self.edit_original_interaction_response = AsyncMock(return_value={"id": "123"})
        self.edit_followup_message = AsyncMock(return_value={"id": "123"})


class DummyBot:
    def __init__(self):
        self._http = DummyHTTP()
        self.application_id = "app123"
        self._guilds = {}
        self._channels = {}

    def get_guild(self, gid):
        return self._guilds.get(gid)

    async def fetch_channel(self, cid):
        return self._channels.get(cid)


from disagreement.ext.commands.core import CommandContext, Command
from disagreement.enums import MessageFlags, ButtonStyle, ComponentType
from disagreement.models import ActionRow, Button, Container, TextDisplay


@pytest.mark.asyncio
async def test_sends_extra_payload(dummy_bot, interaction):
    ctx = AppCommandContext(dummy_bot, interaction)
    button = Button(style=ButtonStyle.PRIMARY, label="Click", custom_id="a")
    row = ActionRow([button])
    await ctx.send(
        content="hi",
        tts=True,
        components=[row],
        allowed_mentions={"parse": []},
        files=[{"id": 1, "filename": "f.txt"}],
        ephemeral=True,
    )
    dummy_bot._http.create_interaction_response.assert_called_once()
    payload = dummy_bot._http.create_interaction_response.call_args.kwargs[
        "payload"
    ].data.to_dict()
    assert payload["tts"] is True
    assert payload["components"]
    assert payload["allowed_mentions"] == {"parse": []}
    assert payload["attachments"] == [{"id": 1, "filename": "f.txt"}]
    assert payload["flags"] == MessageFlags.EPHEMERAL.value
    await ctx.send_followup(content="again")
    dummy_bot._http.create_followup_message.assert_called_once()


@pytest.mark.asyncio
async def test_second_send_is_followup(dummy_bot, interaction):
    ctx = AppCommandContext(dummy_bot, interaction)
    await ctx.send(content="first")
    await ctx.send_followup(content="second")
    assert dummy_bot._http.create_interaction_response.call_count == 1
    assert dummy_bot._http.create_followup_message.call_count == 1


@pytest.mark.asyncio
async def test_edit_with_components_and_attachments(dummy_bot, interaction):
    ctx = AppCommandContext(dummy_bot, interaction)
    await ctx.send(content="orig")
    row = ActionRow([Button(style=ButtonStyle.PRIMARY, label="B", custom_id="b")])
    await ctx.edit(content="new", components=[row], attachments=[{"id": 1}])
    dummy_bot._http.edit_original_interaction_response.assert_called_once()
    payload = dummy_bot._http.edit_original_interaction_response.call_args.kwargs[
        "payload"
    ]
    assert payload["components"]
    assert payload["attachments"] == [{"id": 1}]


@pytest.mark.asyncio
async def test_send_with_flags(dummy_bot, interaction):
    ctx = AppCommandContext(dummy_bot, interaction)
    await ctx.send(content="hi", flags=MessageFlags.IS_COMPONENTS_V2.value)
    payload = dummy_bot._http.create_interaction_response.call_args.kwargs[
        "payload"
    ].data.to_dict()
    assert payload["flags"] == MessageFlags.IS_COMPONENTS_V2.value


@pytest.mark.asyncio
async def test_send_container_component(dummy_bot, interaction):
    ctx = AppCommandContext(dummy_bot, interaction)
    container = Container(components=[TextDisplay(content="hi")])
    await ctx.send(components=[container], flags=MessageFlags.IS_COMPONENTS_V2.value)
    payload = dummy_bot._http.create_interaction_response.call_args.kwargs[
        "payload"
    ].data.to_dict()
    assert payload["components"][0]["type"] == ComponentType.CONTAINER.value
    assert payload["flags"] == MessageFlags.IS_COMPONENTS_V2.value


@pytest.mark.asyncio
async def test_command_context_edit(command_bot, message):
    async def dummy(ctx):
        pass

    cmd = Command(dummy)
    ctx = CommandContext(
        message=message, bot=command_bot, prefix="!", command=cmd, invoked_with="dummy"
    )
    await ctx.edit(message.id, content="new")
    command_bot._http.edit_message.assert_called_once()
    args = command_bot._http.edit_message.call_args[0]
    assert args[0] == message.channel_id
    assert args[1] == message.id
    assert args[2]["content"] == "new"


@pytest.mark.asyncio
async def test_send_http_error_propagates(dummy_bot, interaction):
    ctx = AppCommandContext(dummy_bot, interaction)
    dummy_bot._http.create_interaction_response.side_effect = RuntimeError("boom")
    with pytest.raises(RuntimeError):
        await ctx.send(content="hi")


@pytest.mark.asyncio
async def test_concurrent_send_only_initial_once(dummy_bot, interaction):
    ctx = AppCommandContext(dummy_bot, interaction)

    async def send_msg(i: int):
        if i == 0:
            await ctx.send(content=str(i))
        else:
            await ctx.send_followup(content=str(i))

    await asyncio.gather(*(send_msg(i) for i in range(50)))
    assert dummy_bot._http.create_interaction_response.call_count == 1
    assert dummy_bot._http.create_followup_message.call_count == 49


@pytest.mark.asyncio
async def test_send_with_flags_2():
    bot = DummyBot()
    interaction = Interaction(
        {
            "id": "1",
            "application_id": bot.application_id,
            "type": InteractionType.APPLICATION_COMMAND.value,
            "token": "tok",
            "version": 1,
        },
        client_instance=bot,
    )
    ctx = AppCommandContext(bot, interaction)
    await ctx.send(content="hi", flags=MessageFlags.IS_COMPONENTS_V2.value)
    payload = bot._http.create_interaction_response.call_args[1][
        "payload"
    ].data.to_dict()
    assert payload["flags"] == MessageFlags.IS_COMPONENTS_V2.value


@pytest.mark.asyncio
async def test_send_container_component_2():
    bot = DummyBot()
    interaction = Interaction(
        {
            "id": "1",
            "application_id": bot.application_id,
            "type": InteractionType.APPLICATION_COMMAND.value,
            "token": "tok",
            "version": 1,
        },
        client_instance=bot,
    )
    ctx = AppCommandContext(bot, interaction)
    container = Container(components=[TextDisplay(content="hi")])
    await ctx.send(
        components=[container],
        flags=MessageFlags.IS_COMPONENTS_V2.value,
    )
    payload = bot._http.create_interaction_response.call_args[1][
        "payload"
    ].data.to_dict()
    assert payload["components"][0]["type"] == ComponentType.CONTAINER.value
    assert payload["flags"] == MessageFlags.IS_COMPONENTS_V2.value
