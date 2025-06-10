"""Example bot demonstrating VoiceClient usage."""

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

_VOICE_ENDPOINT = os.getenv("DISCORD_VOICE_ENDPOINT")
_VOICE_TOKEN = os.getenv("DISCORD_VOICE_TOKEN")
_VOICE_SESSION_ID = os.getenv("DISCORD_SESSION_ID")
_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
_USER_ID = os.getenv("DISCORD_USER_ID")

if not all([_VOICE_ENDPOINT, _VOICE_TOKEN, _VOICE_SESSION_ID, _GUILD_ID, _USER_ID]):
    print("Missing one or more required environment variables for voice connection")
    sys.exit(1)

assert _VOICE_ENDPOINT
assert _VOICE_TOKEN
assert _VOICE_SESSION_ID
assert _GUILD_ID
assert _USER_ID

VOICE_ENDPOINT = cast(str, _VOICE_ENDPOINT)
VOICE_TOKEN = cast(str, _VOICE_TOKEN)
VOICE_SESSION_ID = cast(str, _VOICE_SESSION_ID)
GUILD_ID = int(cast(str, _GUILD_ID))
USER_ID = int(cast(str, _USER_ID))


async def main() -> None:
    vc = disagreement.VoiceClient(
        VOICE_ENDPOINT,
        VOICE_SESSION_ID,
        VOICE_TOKEN,
        GUILD_ID,
        USER_ID,
    )
    await vc.connect()

    try:
        # Send silence frame as an example
        await vc.send_audio_frame(b"\xf8\xff\xfe")
        await asyncio.sleep(1)
    finally:
        await vc.close()


if __name__ == "__main__":
    asyncio.run(main())
