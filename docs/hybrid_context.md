# HybridContext

`HybridContext` wraps either a prefix `CommandContext` or a slash `AppCommandContext`. It exposes a single `send` method that proxies to the appropriate reply method for the underlying context.

```python
from disagreement import HybridContext

@commands.command()
async def ping(ctx: commands.CommandContext) -> None:
    hybrid = HybridContext(ctx)
    await hybrid.send("Pong!")
```

It also forwards attribute access to the wrapped context and provides an `edit` helper when supported.
