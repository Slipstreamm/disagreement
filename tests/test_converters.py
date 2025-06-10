import asyncio
import pytest
from hypothesis import given, strategies as st

from disagreement.ext.app_commands.converters import run_converters
from disagreement.enums import ApplicationCommandOptionType
from disagreement.errors import AppCommandOptionConversionError
from conftest import DummyInteraction, DummyClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "py_type, option_type, input_value, expected",
    [
        (str, ApplicationCommandOptionType.STRING, "hello", "hello"),
        (int, ApplicationCommandOptionType.INTEGER, "42", 42),
        (bool, ApplicationCommandOptionType.BOOLEAN, "true", True),
        (float, ApplicationCommandOptionType.NUMBER, "3.14", pytest.approx(3.14)),
    ],
)
async def test_basic_type_converters(
    basic_interaction, dummy_client, py_type, option_type, input_value, expected
):
    result = await run_converters(
        basic_interaction, py_type, option_type, input_value, dummy_client
    )
    assert result == expected


@pytest.mark.asyncio
async def test_run_converters_error_cases(basic_interaction, dummy_client):
    with pytest.raises(AppCommandOptionConversionError):
        await run_converters(
            basic_interaction,
            bool,
            ApplicationCommandOptionType.BOOLEAN,
            "maybe",
            dummy_client,
        )

    with pytest.raises(AppCommandOptionConversionError):
        await run_converters(
            basic_interaction,
            list,
            ApplicationCommandOptionType.MENTIONABLE,
            "x",
            dummy_client,
        )


@given(st.text())
def test_string_roundtrip(value):
    interaction = DummyInteraction()
    client = DummyClient()
    result = asyncio.run(
        run_converters(
            interaction,
            str,
            ApplicationCommandOptionType.STRING,
            value,
            client,
        )
    )
    assert result == value


@given(st.integers())
def test_integer_roundtrip(value):
    interaction = DummyInteraction()
    client = DummyClient()
    result = asyncio.run(
        run_converters(
            interaction,
            int,
            ApplicationCommandOptionType.INTEGER,
            str(value),
            client,
        )
    )
    assert result == value


@given(st.booleans())
def test_boolean_roundtrip(value):
    interaction = DummyInteraction()
    client = DummyClient()
    raw = "true" if value else "false"
    result = asyncio.run(
        run_converters(
            interaction,
            bool,
            ApplicationCommandOptionType.BOOLEAN,
            raw,
            client,
        )
    )
    assert result is value


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_number_roundtrip(value):
    interaction = DummyInteraction()
    client = DummyClient()
    result = asyncio.run(
        run_converters(
            interaction,
            float,
            ApplicationCommandOptionType.NUMBER,
            str(value),
            client,
        )
    )
    assert result == pytest.approx(value)
