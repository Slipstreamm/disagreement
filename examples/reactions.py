# examples/reactions.py

"""
An example bot demonstrating reaction handling with the Disagreement library.

This bot will:
1. React to a specific command with a thumbs-up emoji.
2. Log when any reaction is added to a message in a server it's in.
3. Log when any reaction is removed from a message.

To run this bot:
1. Follow the setup steps in 'basic_bot.py' to set your DISCORD_BOT_TOKEN.
2. Ensure you have the GUILD_MESSAGE_REACTIONS intent enabled for your bot in the Discord Developer Portal.
3. Run this script: python examples/reactions.py
"""

import asyncio
import os
import sys
import logging
import traceback

# Add project root to path for local development
if os.path.join(os.getcwd(), "examples") == os.path.dirname(os.path.abspath(__file__)):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from disagreement import (
        Client,
        GatewayIntent,
        Reaction,
        User,
        Member,
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
# We need GUILDS for server context, GUILD_MESSAGES to receive messages,
# and GUILD_MESSAGE_REACTIONS to listen for reaction events.
intents = (
    GatewayIntent.GUILDS
    | GatewayIntent.GUILD_MESSAGES
    | GatewayIntent.GUILD_MESSAGE_REACTIONS
    | GatewayIntent.MESSAGE_CONTENT  # For commands
)

# --- Initialize the Client ---
if not BOT_TOKEN:
    print("Error: The DISCORD_BOT_TOKEN environment variable is not set.")
    sys.exit(1)

client = Client(token=BOT_TOKEN, intents=intents, command_prefix="!")


# --- Define a Cog for reaction-related commands ---
class ReactionCog(Cog):
    def __init__(self, bot_client):
        super().__init__(bot_client)

    @command(name="react")
    async def react_command(self, ctx: CommandContext):
        """Reacts to the command message with a thumbs up."""
        try:
            # The emoji can be a standard Unicode emoji or a custom one in the format '<:name:id>'
            await ctx.message.add_reaction("👍")
            print(f"Reacted to command from {ctx.author.username}")
        except HTTPException as e:
            print(f"Failed to add reaction: {e}")
            await ctx.reply(
                "I couldn't add the reaction. I might be missing permissions."
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
    print("Reaction example bot is operational.")


@client.on_event("MESSAGE_REACTION_ADD")
async def on_reaction_add(reaction: Reaction, user: User | Member):
    """Called when a message reaction is added."""
    # We can ignore reactions from the bot itself
    if client.user and user.id == client.user.id:
        return

    print(
        f"Reaction '{reaction.emoji}' added by {user.username} "
        f"to message ID {reaction.message_id} in channel ID {reaction.channel_id}"
    )
    # You can fetch the message if you need its content, but it's an extra API call.
    # try:
    #     channel = await client.fetch_channel(reaction.channel_id)
    #     if isinstance(channel, disagreement.TextChannel):
    #         message = await channel.fetch_message(reaction.message_id)
    #         print(f"  Message content: '{message.content}'")
    # except disagreement.errors.NotFound:
    #     print("  Could not fetch message (maybe it was deleted).")


@client.on_event("MESSAGE_REACTION_REMOVE")
async def on_reaction_remove(reaction: Reaction, user: User | Member):
    """Called when a message reaction is removed."""
    print(
        f"Reaction '{reaction.emoji}' removed by {user.username} "
        f"from message ID {reaction.message_id} in channel ID {reaction.channel_id}"
    )


# --- Main Execution ---
async def main():
    print("Starting Reaction Bot...")
    try:
        client.add_cog(ReactionCog(client))
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
