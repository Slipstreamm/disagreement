import pytest

from disagreement.ext.app_commands.handler import AppCommandHandler
from disagreement.ext.app_commands.converters import Converter


class MyType:
    def __init__(self, value):
        self.value = value


class MyConverter(Converter[MyType]):
    async def convert(self, interaction, value):
        return MyType(f"converted-{value}")


@pytest.mark.asyncio
async def test_custom_converter_registration(dummy_client):
    handler = AppCommandHandler(client=dummy_client)
    handler.register_converter(MyType, MyConverter)
    assert handler.get_converter(MyType) is MyConverter

    result = await handler._resolve_value(
        value="example",
        expected_type=MyType,
        resolved_data=None,
        guild_id=None,
    )
    assert isinstance(result, MyType)
    assert result.value == "converted-example"
