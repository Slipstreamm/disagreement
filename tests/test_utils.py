from datetime import datetime, timezone

from disagreement.utils import utcnow, snowflake_time


def test_utcnow_timezone():
    now = utcnow()
    assert now.tzinfo == timezone.utc


def test_snowflake_time():
    dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
    ms = int(dt.timestamp() * 1000) - 1420070400000
    snowflake = ms << 22
    assert snowflake_time(snowflake) == dt
