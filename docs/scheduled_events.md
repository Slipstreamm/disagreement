# Guild Scheduled Events

The `Client` provides helpers to manage guild scheduled events.

```python
from disagreement.client import Client

client = Client(token="TOKEN")

payload = {
    "name": "Movie Night",
    "scheduled_start_time": "2024-05-01T20:00:00Z",
    "privacy_level": 2,
    "entity_type": 3,
    "entity_metadata": {"location": "https://discord.gg/example"},
}

event = await client.create_scheduled_event(123456789012345678, payload)
print(event.id, event.name)
```

## Next Steps

- [Commands](commands.md)
- [Caching](caching.md)
- [Voice Features](voice_features.md)
