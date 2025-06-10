# Commands Extension

This guide covers the built-in prefix command system.

## Help Command

The command handler registers a `help` command automatically. Use it to list all available commands or get information about a single command.

```
!help              # lists commands
!help ping         # shows help for the "ping" command
```

The help command will show each command's brief description if provided.

## Checks

Use `commands.check` to prevent a command from running unless a predicate
returns ``True``. Checks may be regular or async callables that accept a
`CommandContext`.

```python
from disagreement.ext.commands import command, check, CheckFailure

def is_owner(ctx):
    return ctx.author.id == "1"

@command()
@check(is_owner)
async def secret(ctx):
    await ctx.send("Only for the owner!")
```

When a check fails a :class:`CheckFailure` is raised and dispatched through the
command error handler.

## Cooldowns

Commands can be rate limited using the ``cooldown`` decorator. The example
below restricts usage to once every three seconds per user:

```python
from disagreement.ext.commands import command, cooldown

@command()
@cooldown(1, 3.0)
async def ping(ctx):
    await ctx.send("Pong!")
```

Invoking a command while it is on cooldown raises :class:`CommandOnCooldown`.

## Permission Checks

Use `commands.requires_permissions` to ensure the invoking member has the
required permissions in the channel.

```python
from disagreement.ext.commands import command, requires_permissions
from disagreement.permissions import Permissions

@command()
@requires_permissions(Permissions.MANAGE_MESSAGES)
async def purge(ctx):
    await ctx.send("Purged!")
```

Missing permissions raise :class:`CheckFailure`.
