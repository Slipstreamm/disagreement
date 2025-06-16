# Utility Helpers

Disagreement provides a few small utility functions for working with Discord data.

## `utcnow`

Returns the current timezone-aware UTC `datetime`.

## `snowflake_time`

Converts a Discord snowflake ID into the UTC timestamp when it was generated.

```python
from disagreement.utils import snowflake_time

created_at = snowflake_time(175928847299117063)
print(created_at.isoformat())
```

The function extracts the timestamp from the snowflake and returns a `datetime` in UTC.
