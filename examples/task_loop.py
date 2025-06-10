"""Example showing the tasks extension."""

import asyncio
import os
import sys

# Allow running from the examples folder without installing
if os.path.join(os.getcwd(), "examples") == os.path.dirname(os.path.abspath(__file__)):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from disagreement.ext import tasks

counter = 0


@tasks.loop(seconds=1.0)
async def ticker() -> None:
    global counter
    counter += 1
    print(f"Tick {counter}")


async def main() -> None:
    ticker.start()
    await asyncio.sleep(5)
    ticker.stop()


if __name__ == "__main__":
    asyncio.run(main())
