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

