# Caching

Disagreement ships with a simple in-memory cache used by the HTTP and Gateway clients. Cached objects reduce API requests and improve performance.

The client automatically caches guilds, channels and users as they are received from events or HTTP calls. You can access cached data through lookup helpers such as `Client.get_guild`.

Once you have a `Guild` object you can look up its cached members. `Guild.get_member` retrieves a member by ID, while `Guild.get_member_named` searches by username or nickname:

```python
guild = client.get_guild(123456789012345678)
member = guild.get_member_named("Slipstream")
if member:
    print(member.id)
```

The cache can be cleared manually if needed:

```python
client.cache.clear()
```

## Next Steps

- [Components](using_components.md)
- [Slash Commands](slash_commands.md)
- [Voice Features](voice_features.md)

