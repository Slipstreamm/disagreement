from datetime import datetime, timezone
from types import SimpleNamespace

from disagreement.utils import (
    escape_markdown,
    escape_mentions,
    utcnow,
    snowflake_time,
    find,
    get
)


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


def test_snowflake_time():
    dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
    ms = int(dt.timestamp() * 1000) - 1420070400000
    snowflake = ms << 22
    assert snowflake_time(snowflake) == dt


def test_escape_markdown():
    text = "**bold** _under_ ~strike~ `code` > quote | pipe"
    escaped = escape_markdown(text)
    assert (
        escaped
        == "\\*\\*bold\\*\\* \\_under\\_ \\~strike\\~ \\`code\\` \\> quote \\| pipe"
    )


def test_escape_mentions():
    text = "Hello @everyone and <@123>!"
    escaped = escape_mentions(text)
    assert escaped == "Hello @\u200beveryone and <@\u200b123>!"
