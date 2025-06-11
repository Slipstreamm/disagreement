# Using Slash Commands

The library provides a slash command framework via the `ext.app_commands` package. Define commands with decorators and register them with Discord.

```python
from disagreement.ext.app_commands import AppCommandGroup

bot_commands = AppCommandGroup("bot", "Bot commands")

@bot_commands.command(name="ping")
async def ping(ctx):
    await ctx.respond("Pong!")
```

Use `AppCommandGroup` to group related commands. See the [components guide](using_components.md) for building interactive responses.

## Next Steps

- [Components](using_components.md)
- [Caching](caching.md)
- [Voice Features](voice_features.md)
- [HTTP Client Options](http_client.md)

## Command Persistence

`AppCommandHandler.sync_commands` can persist registered command IDs in
`.disagreement_commands.json`. When enabled, subsequent syncs compare the
stored IDs to the commands defined in code and only create, edit or delete
commands when changes are detected.

Call `AppCommandHandler.clear_stored_registrations()` if you need to wipe the
stored IDs or migrate them elsewhere with
`AppCommandHandler.migrate_stored_registrations()`.

