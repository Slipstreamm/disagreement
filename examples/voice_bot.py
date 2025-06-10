"""Example bot demonstrating voice channel playback."""

import os
import asyncio
import sys

# If running from the examples directory
if os.path.join(os.getcwd(), "examples") == os.path.dirname(os.path.abspath(__file__)):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import cast

from dotenv import load_dotenv

import disagreement

load_dotenv()

_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
_CHANNEL_ID = os.getenv("DISCORD_VOICE_CHANNEL")

if not all([_TOKEN, _GUILD_ID, _CHANNEL_ID]):
    print("Missing one or more required environment variables for voice connection")
    sys.exit(1)

assert _TOKEN
assert _GUILD_ID
assert _CHANNEL_ID

TOKEN = cast(str, _TOKEN)
GUILD_ID = cast(str, _GUILD_ID)
CHANNEL_ID = cast(str, _CHANNEL_ID)


async def main() -> None:
    client = disagreement.Client(TOKEN)
    await client.connect()
    voice = await client.join_voice(GUILD_ID, CHANNEL_ID)
    try:
        await voice.play_file("welcome.mp3")
    finally:
        await voice.close()
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
