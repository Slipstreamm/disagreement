import pytest

from disagreement.enums import GatewayIntent


def test_gateway_intent_none_equals_zero():
    assert GatewayIntent.none() == 0
