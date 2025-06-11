# Example from the README file of the disagreement library
# This example demonstrates a simple bot that responds to the "!ping" command with "Pong!".

import asyncio
import os

import disagreement
from disagreement.ext import commands
from dotenv import load_dotenv

load_dotenv()


class Basics(commands.Cog):
    def __init__(self, client: disagreement.Client) -> None:
        super().__init__(client)

    @commands.command()
    async def ping(self, ctx: commands.CommandContext) -> None:
        await ctx.reply(f"Pong! Gateway Latency: {self.client.latency_ms} ms.")  # type: ignore (latency is None during static analysis)


token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    raise RuntimeError("DISCORD_BOT_TOKEN environment variable not set")

intents = (
    disagreement.GatewayIntent.default() | disagreement.GatewayIntent.MESSAGE_CONTENT
)
client = disagreement.Client(
    token=token, command_prefix="!", intents=intents, mention_replies=True
)


async def main() -> None:
    client.add_cog(Basics(client))
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
