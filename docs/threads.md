# Threads

`Message.create_thread` and `TextChannel.create_thread` let you start new threads.
Use :class:`AutoArchiveDuration` to control when a thread is automatically archived.

```python
from disagreement.enums import AutoArchiveDuration

await message.create_thread(
    "discussion",
    auto_archive_duration=AutoArchiveDuration.DAY,
)
```

## Next Steps

- [Message History](message_history.md)
- [Caching](caching.md)
