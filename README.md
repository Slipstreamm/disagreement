# Disagreement

A Python library for interacting with the Discord API, with a focus on bot development.

## Features

- Asynchronous design using `aiohttp`
- Gateway and HTTP API clients
- Slash command framework
- Message component helpers
- Built-in caching layer
- Experimental voice support
- Helpful error handling utilities

## Installation

```bash
python -m pip install -U pip
pip install disagreement
# or install from source for development
pip install -e .
```

Requires Python 3.10 or newer.

## Basic Usage

```python
import asyncio
import os

import disagreement
from disagreement.ext import commands


class Basics(commands.Cog):
    def __init__(self, client: disagreement.Client) -> None:
        super().__init__(client)

    @commands.command()
    async def ping(self, ctx: commands.CommandContext) -> None:
        await ctx.reply("Pong!")


token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    raise RuntimeError("DISCORD_BOT_TOKEN environment variable not set")

client = disagreement.Client(token=token, command_prefix="!")
client.add_cog(Basics(client))


async def main() -> None:
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
```

### Global Error Handling

To ensure unexpected errors don't crash your bot, you can enable the library's
global error handler:

```python
import disagreement

disagreement.setup_global_error_handler()
```

Call this early in your program to log unhandled exceptions instead of letting
them terminate the process.

### Configuring Logging

Use :func:`disagreement.logging_config.setup_logging` to configure logging for
your bot. The helper accepts a logging level and an optional file path.

```python
import logging
from disagreement.logging_config import setup_logging

setup_logging(logging.INFO)
# Or log to a file
setup_logging(logging.DEBUG, file="bot.log")
```

### Defining Subcommands with `AppCommandGroup`

```python
from disagreement.ext.app_commands import AppCommandGroup, slash_command
from disagreement.ext.app_commands.context import AppCommandContext

settings_group = AppCommandGroup("settings", "Manage settings")
admin_group = AppCommandGroup("admin", "Admin settings", parent=settings_group)


@slash_command(name="show", description="Display a setting.", parent=settings_group)
async def show(ctx: AppCommandContext, key: str):
    ...


@slash_command(name="set", description="Update a setting.", parent=admin_group)
async def set_setting(ctx: AppCommandContext, key: str, value: str):
    ...
## Fetching Guilds

Use `Client.fetch_guild` to retrieve a guild from the Discord API if it
isn't already cached. This is useful when working with guild IDs from
outside the gateway events.

```python
guild = await client.fetch_guild("123456789012345678")
roles = await client.fetch_roles(guild.id)
```

## Sharding

To run your bot across multiple gateway shards, pass ``shard_count`` when creating
the client:

```python
client = disagreement.Client(token=BOT_TOKEN, shard_count=2)
```

If you want the library to determine the recommended shard count automatically,
use ``AutoShardedClient``:

```python
client = disagreement.AutoShardedClient(token=BOT_TOKEN)
```

See `examples/sharded_bot.py` for a full example.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

See the [docs](docs/) directory for detailed guides on components, slash commands, caching, and voice features.

## License

This project is licensed under the BSD 3-Clause license. See the [LICENSE](LICENSE) file for details.

