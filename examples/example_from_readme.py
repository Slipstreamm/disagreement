# Example from the README file of the disagreement library
# This example demonstrates a simple bot that responds to the "!ping" command with "Pong!".

import asyncio
import os

from disagreement import Client, GatewayIntent, Cog, command, CommandContext
from dotenv import load_dotenv

load_dotenv()


class Basics(Cog):
    def __init__(self, client: Client) -> None:
        super().__init__(client)

    @command()
    async def ping(self, ctx: CommandContext) -> None:
        await ctx.reply(f"Pong! Gateway Latency: {self.client.latency_ms} ms.")  # type: ignore (latency is None during static analysis)


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
