"""Example moderation bot using the Disagreement library."""

import asyncio
import os
import sys
from typing import Set

# Allow running example from repository root
if os.path.join(os.getcwd(), "examples") == os.path.dirname(os.path.abspath(__file__)):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from disagreement import Client, GatewayIntent, Member, Message, Cog, command, CommandContext

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - example helper
    load_dotenv = None
    print("python-dotenv is not installed. Environment variables will not be loaded")

if load_dotenv:
    load_dotenv()

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not BOT_TOKEN:
    print("DISCORD_BOT_TOKEN environment variable not set")
    sys.exit(1)

intents = (
    GatewayIntent.GUILDS
    | GatewayIntent.GUILD_MESSAGES
    | GatewayIntent.MESSAGE_CONTENT
)
client = Client(token=BOT_TOKEN, command_prefix="!", intents=intents)

# Simple list of banned words
BANNED_WORDS: Set[str] = {"badword1", "badword2"}


class ModerationCog(Cog):
    def __init__(self, bot: Client) -> None:
        super().__init__(bot)

    @command()
    async def kick(
        self, ctx: CommandContext, member: Member, *, reason: str = ""
    ) -> None:
        """Kick a member from the guild."""
        await member.kick(reason=reason or None)
        await ctx.reply(f"Kicked {member.display_name}")

    @command()
    async def ban(
        self, ctx: CommandContext, member: Member, *, reason: str = ""
    ) -> None:
        """Ban a member from the guild."""
        await member.ban(reason=reason or None)
        await ctx.reply(f"Banned {member.display_name}")


@client.event
async def on_ready() -> None:
    if client.user:
        print(f"Logged in as {client.user.username}#{client.user.discriminator}")
    print("Moderation bot ready.")


@client.event
async def on_message(message: Message) -> None:
    await client._process_message_for_commands(message)
    if message.author.bot:
        return
    content_lower = message.content.lower()
    if any(word in content_lower for word in BANNED_WORDS):
        await message.delete()
        await client.send_message(
            message.channel_id,
            f"{message.author.mention}, your message was removed for inappropriate content.",
        )


async def main() -> None:
    client.add_cog(ModerationCog(client))
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
