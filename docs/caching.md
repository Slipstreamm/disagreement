# Caching

Disagreement ships with a simple in-memory cache used by the HTTP and Gateway clients. Cached objects reduce API requests and improve performance.

The client automatically caches guilds, channels and users as they are received from events or HTTP calls. You can access cached data through lookup helpers such as `Client.get_guild`.

Once you have a `Guild` object you can look up its cached members. `Guild.get_member` retrieves a member by ID, while `Guild.get_member_named` searches by username or nickname:

```python
guild = client.get_guild(123456789012345678)
member = guild.get_member_named("Slipstream")
if member:
    print(member.display_name)
```

To access the bot's own member object, use the ``Guild.me`` property. It returns
``None`` if the bot is not in the guild or its user data hasn't been loaded:

```python
bot_member = guild.me
if bot_member:
    print(bot_member.joined_at)
```

The cache can be cleared manually if needed:

```python
client.cache.clear()
```

## Partial Objects

Some events only include minimal data for related resources. When only an ``id``
is available, Disagreement represents the resource using :class:`~disagreement.Object`.
These objects can be compared and used in sets or dictionaries and can be passed
to API methods to fetch the full data when needed.

## Next Steps

- [Components](using_components.md)
- [Slash Commands](slash_commands.md)
- [Voice Features](voice_features.md)
- [HTTP Client Options](http_client.md)

