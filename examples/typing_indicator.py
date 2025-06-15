# examples/typing_indicator.py

"""
An example bot demonstrating how to use the typing indicator with the Disagreement library.

This bot will:
1. Respond to a command `!typing_test`.
2. Send a typing indicator to the channel where the command was invoked.
3. Simulate a long-running task while the typing indicator is active.

To run this bot:
1. Follow the setup steps in 'basic_bot.py' to set your DISCORD_BOT_TOKEN.
2. Ensure you have the necessary intents (GUILDS, GUILD_MESSAGES, MESSAGE_CONTENT).
3. Run this script: python examples/typing_indicator.py
"""

import asyncio
import os
import sys
import traceback

# Add project root to path for local development
if os.path.join(os.getcwd(), "examples") == os.path.dirname(os.path.abspath(__file__)):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from disagreement import (
        Client,
        GatewayIntent,
        HTTPException,
        AuthenticationError,
        Cog,
        command,
        CommandContext,
    )
except ImportError:
    print(
        "Failed to import disagreement. Make sure it's installed or PYTHONPATH is set correctly."
    )
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - example helper
    load_dotenv = None
    print("python-dotenv is not installed. Environment variables will not be loaded")

if load_dotenv:
    load_dotenv()

# --- Bot Configuration ---
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

# --- Intents Configuration ---
intents = (
    GatewayIntent.GUILDS
    | GatewayIntent.GUILD_MESSAGES
    | GatewayIntent.MESSAGE_CONTENT
)

# --- Initialize the Client ---
if not BOT_TOKEN:
    print("Error: The DISCORD_BOT_TOKEN environment variable is not set.")
    sys.exit(1)

client = Client(token=BOT_TOKEN, intents=intents, command_prefix="!")


# --- Define a Cog for the typing indicator command ---
class TypingCog(Cog):
    def __init__(self, bot_client):
        super().__init__(bot_client)

    @command(name="typing")
    async def typing_test_command(self, ctx: CommandContext):
        """Shows a typing indicator for 5 seconds."""
        await ctx.reply("Showing typing indicator for 5 seconds...")
        try:
            async with client.typing(ctx.message.channel_id):
                print(
                    f"Displaying typing indicator in channel {ctx.message.channel_id} for 5 seconds."
                )
                await asyncio.sleep(5)
            print("Typing indicator stopped.")
            await ctx.send("Done!")
        except HTTPException as e:
            print(f"Failed to send typing indicator: {e}")
            await ctx.reply(
                "I couldn't show the typing indicator. I might be missing permissions."
            )


# --- Event Handlers ---


@client.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    if client.user:
        print(f"Bot is ready! Logged in as {client.user.username}")
    else:
        print("Bot is ready, but client.user is missing!")
    print("------")
    print("Typing indicator example bot is operational.")
    print("Use the `!typing_test` command in a server channel.")


# --- Main Execution ---
async def main():
    print("Starting Typing Indicator Bot...")
    try:
        client.add_cog(TypingCog(client))
        await client.run()
    except AuthenticationError:
        print("Authentication failed. Check your bot token.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()
    finally:
        if not client.is_closed():
            await client.close()
        print("Bot has been shut down.")


if __name__ == "__main__":
    asyncio.run(main())
