from datetime import timezone

from types import SimpleNamespace

from disagreement.utils import utcnow, find, get


def test_utcnow_timezone():
    now = utcnow()
    assert now.tzinfo == timezone.utc


def test_find_returns_matching_element():
    seq = [1, 2, 3]
    assert find(lambda x: x > 1, seq) == 2
    assert find(lambda x: x > 3, seq) is None


def test_get_matches_attributes():
    items = [
        SimpleNamespace(id=1, name="a"),
        SimpleNamespace(id=2, name="b"),
    ]
    assert get(items, id=2) is items[1]
    assert get(items, id=1, name="a") is items[0]
    assert get(items, name="c") is None
