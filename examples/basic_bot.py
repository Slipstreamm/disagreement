# examples/basic_bot.py

"""
A basic example bot using the Disagreement library.

To run this bot:
1. Make sure you have the 'disagreement' library installed or accessible in your PYTHONPATH.
   If running from the project root, it should be discoverable.
2. Set the DISCORD_BOT_TOKEN environment variable to your bot's token.
   e.g., export DISCORD_BOT_TOKEN="your_actual_token_here" (Linux/macOS)
         set DISCORD_BOT_TOKEN="your_actual_token_here" (Windows CMD)
         $env:DISCORD_BOT_TOKEN="your_actual_token_here" (Windows PowerShell)
3. Run this script: python examples/basic_bot.py
"""

import asyncio
import os
import logging  # Optional: for more detailed logging

# Assuming the 'disagreement' package is in the parent directory or installed
import sys
import traceback

# Add project root to path if running script directly from examples folder
# and disagreement is not installed
if os.path.join(os.getcwd(), "examples") == os.path.dirname(os.path.abspath(__file__)):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import disagreement
    from disagreement.models import Guild
    from disagreement.ext import commands  # Import the new commands extension
except ImportError:
    print(
        "Failed to import disagreement. Make sure it's installed or PYTHONPATH is set correctly."
    )
    print(
        "If running from the 'examples' directory, try running from the project root: python -m examples.basic_bot"
    )
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

# Optional: Configure logging for more insight, especially for gateway events
# logging.basicConfig(level=logging.DEBUG) # For very verbose output
# logging.getLogger('disagreement.gateway').setLevel(logging.INFO) # Or DEBUG
# logging.getLogger('disagreement.http').setLevel(logging.INFO)

# --- Bot Configuration ---
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

# --- Intents Configuration ---
# Define the intents your bot needs. For basic message reading and responding:
intents = (
    disagreement.GatewayIntent.GUILDS
    | disagreement.GatewayIntent.GUILD_MESSAGES
    | disagreement.GatewayIntent.MESSAGE_CONTENT
)  # MESSAGE_CONTENT is privileged!

# If you don't need message content and only react to commands/mentions,
# you might not need MESSAGE_CONTENT intent.
# intents = disagreement.GatewayIntent.default() # A good starting point without privileged intents
# intents |= disagreement.GatewayIntent.MESSAGE_CONTENT # Add if needed

# --- Initialize the Client ---
if not BOT_TOKEN:
    print("Error: The DISCORD_BOT_TOKEN environment variable is not set.")
    print("Please set it before running the bot.")
    sys.exit(1)

# Initialize Client with a command prefix
client = disagreement.Client(token=BOT_TOKEN, intents=intents, command_prefix="!")


# --- Define a Cog for example commands ---
class ExampleCog(commands.Cog):  # Ensuring this uses commands.Cog
    def __init__(
        self, bot_client
    ):  # Renamed client to bot_client to avoid conflict with self.client
        super().__init__(bot_client)  # Pass the client instance to the base Cog

    @commands.command(name="hello", aliases=["hi"])
    async def hello_command(self, ctx: commands.CommandContext, *, who: str = "world"):
        """Greets someone."""
        await ctx.reply(f"Hello {ctx.author.mention} and {who}!")
        print(f"Executed 'hello' command for {ctx.author.username}, greeting {who}")

    @commands.command()
    async def ping(self, ctx: commands.CommandContext):
        """Responds with Pong!"""
        await ctx.reply("Pong!")
        print(f"Executed 'ping' command for {ctx.author.username}")

    @commands.command()
    async def me(self, ctx: commands.CommandContext):
        """Shows information about the invoking user."""
        reply_content = (
            f"Hello {ctx.author.mention}!\n"
            f"Your User ID is: {ctx.author.id}\n"
            f"Your Username: {ctx.author.username}#{ctx.author.discriminator}\n"
            f"Are you a bot? {'Yes' if ctx.author.bot else 'No'}"
        )
        await ctx.reply(reply_content)
        print(f"Executed 'me' command for {ctx.author.username}")

    @commands.command(name="add")
    async def add_numbers(self, ctx: commands.CommandContext, num1: int, num2: int):
        """Adds two numbers."""
        result = num1 + num2
        await ctx.reply(f"The sum of {num1} and {num2} is {result}.")
        print(
            f"Executed 'add' command for {ctx.author.username}: {num1} + {num2} = {result}"
        )

    @commands.command(name="say")
    async def say_something(self, ctx: commands.CommandContext, *, text_to_say: str):
        """Repeats the text you provide."""
        await ctx.reply(f"You said: {text_to_say}")
        print(
            f"Executed 'say' command for {ctx.author.username}, saying: {text_to_say}"
        )

    @commands.command(name="whois")
    async def whois(self, ctx: commands.CommandContext, *, name: str):
        """Looks up a member by username or nickname using the guild cache."""
        if not ctx.guild:
            await ctx.reply("This command can only be used in a guild.")
            return

        member = ctx.guild.get_member_named(name)
        if member:
            await ctx.reply(
                f"Found: {member.username}#{member.discriminator} (display: {member.display_name})"
            )
        else:
            await ctx.reply("Member not found in cache.")

    @commands.command(name="quit")
    async def quit_command(self, ctx: commands.CommandContext):
        """Shuts down the bot (requires YOUR_USER_ID to be set)."""
        # Replace YOUR_USER_ID with your actual Discord User ID for a safe shutdown command
        your_user_id = "YOUR_USER_ID_REPLACE_ME"  # IMPORTANT: Replace this
        if str(ctx.author.id) == your_user_id:
            print("Quit command received. Shutting down...")
            await ctx.reply("Shutting down...")
            await self.client.close()  # Access client via self.client from Cog
        else:
            await ctx.reply("You are not authorized to use this command.")
            print(
                f"Unauthorized quit attempt by {ctx.author.username} ({ctx.author.id})"
            )


# --- Event Handlers ---


@client.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    if client.user:
        print(
            f"Bot is ready! Logged in as {client.user.username}#{client.user.discriminator}"
        )
        print(f"User ID: {client.user.id}")
    else:
        print("Bot is ready, but client.user is missing!")
    print("------")
    print("Disagreement Bot is operational.")
    print("Listening for commands...")


@client.event
async def on_message(message: disagreement.Message):
    """Called when a message is created and received."""
    # Command processing is now handled by the CommandHandler via client._process_message_for_commands
    # This on_message can be used for other message-related logic if needed,
    # or removed if all message handling is command-based.

    # Example: Log all messages (excluding bot's own, if client.user was available)
    # if client.user and message.author.id == client.user.id:
    #     return

    print(
        f"General on_message: #{message.channel_id} from {message.author.username}: {message.content}"
    )
    # The old if/elif command structure is no longer needed here.


@client.on_event(
    "GUILD_CREATE"
)  # Example of listening to a specific event by its Discord name
async def on_guild_available(guild: Guild):
    # The event now passes a Guild object directly
    print(f"Guild available: {guild.name} (ID: {guild.id})")


# --- Main Execution ---
async def main():
    print("Starting Disagreement Bot...")
    try:
        # Add the Cog to the client
        client.add_cog(ExampleCog(client))  # Pass client instance to Cog constructor
        # client.add_cog is synchronous, but it schedules cog.cog_load() if it's async.

        await client.run()
    except disagreement.AuthenticationError:
        print(
            "Authentication failed. Please check your bot token and ensure it's correct."
        )
    except disagreement.DisagreementException as e:
        print(f"A Disagreement library error occurred: {e}")
    except KeyboardInterrupt:
        print("Bot shutting down due to KeyboardInterrupt...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()
    finally:
        if not client.is_closed():
            print("Ensuring client is closed...")
            await client.close()
        print("Bot has been shut down.")


if __name__ == "__main__":
    # Note: On Windows, the default asyncio event loop policy might not support add_signal_handler.
    # If you encounter issues with Ctrl+C not working as expected,
    # you might need to adjust the event loop policy or handle shutdown differently.
    # For example, for Windows:
    # if os.name == 'nt':
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
