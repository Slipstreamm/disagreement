import pytest

from disagreement.permissions import (
    Permissions,
    has_permissions,
    missing_permissions,
    permissions_value,
)


def test_permissions_value_combination():
    perm = permissions_value(Permissions.SEND_MESSAGES, Permissions.MANAGE_MESSAGES)
    assert perm == (Permissions.SEND_MESSAGES | Permissions.MANAGE_MESSAGES)


def test_has_permissions_true():
    current = Permissions.SEND_MESSAGES | Permissions.MANAGE_MESSAGES
    assert has_permissions(current, Permissions.SEND_MESSAGES)
    assert has_permissions(
        current, Permissions.MANAGE_MESSAGES, Permissions.SEND_MESSAGES
    )


def test_has_permissions_false():
    current = Permissions.SEND_MESSAGES
    assert not has_permissions(current, Permissions.MANAGE_MESSAGES)


def test_missing_permissions():
    current = Permissions.SEND_MESSAGES
    missing = missing_permissions(
        current, Permissions.SEND_MESSAGES, Permissions.MANAGE_MESSAGES
    )
    assert missing == [Permissions.MANAGE_MESSAGES]
