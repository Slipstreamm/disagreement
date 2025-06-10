"""Example showing how to read a channel's message history."""

import asyncio
import os
import sys

# Allow running example from repository root
if os.path.join(os.getcwd(), "examples") == os.path.dirname(os.path.abspath(__file__)):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from disagreement.client import Client
from disagreement.models import TextChannel
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID", "")

client = Client(token=BOT_TOKEN)


async def main() -> None:
    channel = await client.fetch_channel(CHANNEL_ID)
    if isinstance(channel, TextChannel):
        async for message in channel.history(limit=10):
            print(message.content)


if __name__ == "__main__":
    asyncio.run(main())
