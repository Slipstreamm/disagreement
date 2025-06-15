# Disagreement

A Python library for interacting with the Discord API, with a focus on bot development.

## Features

- Asynchronous design using `aiohttp`
- Gateway and HTTP API clients
- Slash command framework
- Message component helpers
- Internationalization helpers
- Hybrid context for commands
- Built-in rate limiting
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

To run the example scripts, you'll need the `python-dotenv` package to load
environment variables. Install the development extras with:

```bash
pip install "disagreement[dev]"
```

## Basic Usage

```python
import asyncio
import os

from disagreement import Client, GatewayIntent
from disagreement.ext import commands
from dotenv import load_dotenv
load_dotenv()


class Basics(commands.Cog):
    def __init__(self, client: Client) -> None:
        super().__init__(client)

    @commands.command()
    async def ping(self, ctx: commands.CommandContext) -> None:
        await ctx.reply(f"Pong! Gateway Latency: {self.client.latency_ms} ms.")


token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    raise RuntimeError("DISCORD_BOT_TOKEN environment variable not set")

intents = GatewayIntent.default() | GatewayIntent.MESSAGE_CONTENT
client = Client(token=token, command_prefix="!", intents=intents, mention_replies=True)
async def main() -> None:
    client.add_cog(Basics(client))
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

### HTTP Session Options

Pass additional keyword arguments to ``aiohttp.ClientSession`` using the
``http_options`` parameter when constructing :class:`Client`:

```python
client = Client(
    token=token,
    http_options={"proxy": "http://localhost:8080"},
)
```

These options are forwarded to ``HTTPClient`` when it creates the underlying
``aiohttp.ClientSession``. You can specify a custom ``connector`` or any other
session parameter supported by ``aiohttp``.

### Default Allowed Mentions

Specify default mention behaviour for all outgoing messages when constructing the client:

```python
from disagreement.models import AllowedMentions
client = Client(
    token=token,
    allowed_mentions=AllowedMentions.none().to_dict(),
)
```

This dictionary is used whenever ``send_message`` or helpers like ``Message.reply``
are called without an explicit ``allowed_mentions`` argument.

The :class:`AllowedMentions` class offers ``none()`` and ``all()`` helpers for
quickly generating these configurations.

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
```
## Fetching Guilds

Use `Client.fetch_guild` to retrieve a guild from the Discord API if it
isn't already cached. This is useful when working with guild IDs from
outside the gateway events.

```python
guild = await client.fetch_guild("123456789012345678")
roles = await client.fetch_roles(guild.id)
```

To retrieve all guilds available to the bot, use `Client.fetch_guilds`.

```python
guilds = await client.fetch_guilds()
```

## Sharding

To run your bot across multiple gateway shards, pass ``shard_count`` when creating
the client:

```python
client = Client(token=BOT_TOKEN, shard_count=2)
```

If you want the library to determine the recommended shard count automatically,
use ``AutoShardedClient``:

```python
from disagreement import AutoShardedClient
client = AutoShardedClient(token=BOT_TOKEN)
```

See `examples/sharded_bot.py` for a full example.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

See the [documentation home](index.md) for detailed guides on components, slash commands, caching, and voice features.

## License

This project is licensed under the BSD 3-Clause license. See the [LICENSE](https://github.com/your-username/disagreement/blob/main/LICENSE) file for details.