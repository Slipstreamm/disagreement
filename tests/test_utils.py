from datetime import timezone

from disagreement.utils import utcnow


def test_utcnow_timezone():
    now = utcnow()
    assert now.tzinfo == timezone.utc
