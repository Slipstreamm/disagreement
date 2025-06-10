import pytest

from disagreement.ext.app_commands.handler import AppCommandHandler
from disagreement.ext.app_commands.decorators import user_command, message_command
from disagreement.enums import ApplicationCommandType, InteractionType
from disagreement.interactions import Interaction
from disagreement.models import User, Message


@pytest.mark.asyncio
async def test_user_context_menu_invokes(dummy_bot):
    handler = AppCommandHandler(dummy_bot)
    captured = {}

    @user_command(name="Info")
    async def info(ctx, user: User):
        captured["user"] = user

    handler.add_command(info)

    data = {
        "id": "cmd",
        "name": "Info",
        "type": ApplicationCommandType.USER.value,
        "target_id": "42",
        "resolved": {
            "users": {"42": {"id": "42", "username": "Bob", "discriminator": "0001"}}
        },
    }
    payload = {
        "id": "1",
        "application_id": dummy_bot.application_id,
        "type": InteractionType.APPLICATION_COMMAND.value,
        "token": "tok",
        "version": 1,
        "data": data,
    }
    interaction = Interaction(payload, client_instance=dummy_bot)
    await handler.process_interaction(interaction)
    assert isinstance(captured.get("user"), User)
    assert captured["user"].id == "42"


@pytest.mark.asyncio
async def test_message_context_menu_invokes(dummy_bot):
    handler = AppCommandHandler(dummy_bot)
    captured = {}

    @message_command(name="Quote")
    async def quote(ctx, message: Message):
        captured["msg"] = message

    handler.add_command(quote)

    msg_data = {
        "id": "99",
        "channel_id": "c",
        "author": {"id": "2", "username": "Ann", "discriminator": "0001"},
        "content": "Hello",
        "timestamp": "t",
    }
    data = {
        "id": "cmd",
        "name": "Quote",
        "type": ApplicationCommandType.MESSAGE.value,
        "target_id": "99",
        "resolved": {"messages": {"99": msg_data}},
    }
    payload = {
        "id": "1",
        "application_id": dummy_bot.application_id,
        "type": InteractionType.APPLICATION_COMMAND.value,
        "token": "tok",
        "version": 1,
        "data": data,
    }
    interaction = Interaction(payload, client_instance=dummy_bot)
    await handler.process_interaction(interaction)
    assert isinstance(captured.get("msg"), Message)
    assert captured["msg"].id == "99"
