"""Example bot demonstrating gateway sharding."""

import asyncio
import os
import sys

# Ensure local package is importable when running from the examples directory
if os.path.join(os.getcwd(), "examples") == os.path.dirname(os.path.abspath(__file__)):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from disagreement import Client

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - example helper
    load_dotenv = None
    print("python-dotenv is not installed. Environment variables will not be loaded")

if load_dotenv:
    load_dotenv()

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN environment variable not set")

client = Client(token=TOKEN, shard_count=2)


@client.event
async def on_ready():
    if client.user:
        print(f"Shard bot ready as {client.user.username}#{client.user.discriminator}")
    else:
        print("Shard bot ready")


async def main():
    if not TOKEN:
        print("DISCORD_BOT_TOKEN environment variable not set")
        return
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
