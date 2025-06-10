"""Demonstrates dynamic extension loading using Client.load_extension."""

import asyncio
import os
import sys

from dotenv import load_dotenv

# Allow running from the examples folder without installing
if os.path.join(os.getcwd(), "examples") == os.path.dirname(os.path.abspath(__file__)):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from disagreement import Client

load_dotenv()

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")


async def main() -> None:
    if not TOKEN:
        print("DISCORD_BOT_TOKEN environment variable not set")
        return

    client = Client(token=TOKEN)

    # Load the extension which starts a simple ticker task
    client.load_extension("examples.sample_extension")

    await client.connect()
    await asyncio.sleep(6)

    # Reload the extension to restart the ticker
    client.reload_extension("examples.sample_extension")
    await asyncio.sleep(6)

    # Unload the extension and stop the ticker
    client.unload_extension("examples.sample_extension")

    await asyncio.sleep(1)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
