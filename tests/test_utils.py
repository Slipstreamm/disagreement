from datetime import datetime, timezone

from disagreement.utils import (
    escape_markdown,
    escape_mentions,
    utcnow,
    snowflake_time
)


def test_utcnow_timezone():
    now = utcnow()
    assert now.tzinfo == timezone.utc


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
