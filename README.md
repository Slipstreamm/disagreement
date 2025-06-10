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

Requires Python 3.11 or newer.

## Basic Usage

```python
import asyncio
import os
import disagreement

# Ensure DISCORD_BOT_TOKEN is set in your environment
client = disagreement.Client(token=os.environ.get("DISCORD_BOT_TOKEN"))

@client.on_event('MESSAGE_CREATE')
async def on_message(message: disagreement.Message):
    print(f"Received: {message.content} from {message.author.username}")
    if message.content.lower() == '!ping':
        await message.reply('Pong!')

async def main():
    if not client.token:
        print("Error: DISCORD_BOT_TOKEN environment variable not set.")
        return
    try:
        async with client:
            await asyncio.Future()  # run until cancelled
    except KeyboardInterrupt:
        print("Bot shutting down...")
    # Add any other specific exception handling from your library, e.g., disagreement.AuthenticationError

if __name__ == '__main__':
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
from disagreement.ext.app_commands import AppCommandGroup

settings = AppCommandGroup("settings", "Manage settings")

@settings.command(name="show")
async def show(ctx):
    """Displays a setting."""
    ...

@settings.group("admin", description="Admin settings")
def admin_group():
    pass

@admin_group.command(name="set")
async def set_setting(ctx, key: str, value: str):
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

To run your bot across multiple gateway shards, pass `shard_count` when creating
the client:

```python
client = disagreement.Client(token=BOT_TOKEN, shard_count=2)
```

See `examples/sharded_bot.py` for a full example.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

See the [docs](docs/) directory for detailed guides on components, slash commands, caching, and voice features.

