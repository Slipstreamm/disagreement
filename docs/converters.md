# Command Argument Converters

`disagreement.ext.commands` provides a number of built in converters that will parse string arguments into richer objects. These converters are automatically used when a command callback annotates its parameters with one of the supported types.

## Supported Types

- `int`, `float`, `bool`, and `str`
- `Member` – resolves a user mention or ID to a `Member` object for the current guild
- `Role` – resolves a role mention or ID to a `Role` object
- `Guild` – resolves a guild ID to a `Guild` object

## Example

```python
from disagreement.ext.commands import command
from disagreement.ext.commands.core import CommandContext
from disagreement.models import Member

@command()
async def kick(ctx: CommandContext, target: Member):
    await target.kick()
    await ctx.send(f"Kicked {target.display_name}")
```

The framework will automatically convert the first argument to a `Member` using the mention or ID provided by the user.
