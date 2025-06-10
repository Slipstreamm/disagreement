"""Examples showing how to use context menu commands."""

import os
import sys

# Allow running example from repository root
if os.path.join(os.getcwd(), "examples") == os.path.dirname(os.path.abspath(__file__)):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from disagreement.client import Client
from disagreement.ext.app_commands import (
    user_command,
    message_command,
    AppCommandContext,
)
from disagreement.models import User, Message

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
APP_ID = os.environ.get("DISCORD_APPLICATION_ID", "")
client = Client(token=BOT_TOKEN, application_id=APP_ID)


@client.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    if client.user:
        print(f"Bot is ready! Logged in as {client.user.username}")
        print("Attempting to sync application commands...")
        try:
            if client.application_id:
                await client.app_command_handler.sync_commands(
                    application_id=client.application_id
                )
                print("Application commands synced successfully.")
            else:
                print("Skipping command sync: application ID is not set.")
        except Exception as e:
            print(f"Error syncing application commands: {e}")
    else:
        print("Bot is ready, but client.user is missing!")
    print("------")


@user_command(name="User Info")
async def user_info(ctx: AppCommandContext, user: User) -> None:
    await ctx.send(
        f"Selected user: {user.username}#{user.discriminator}", ephemeral=True
    )


@message_command(name="Quote")
async def quote(ctx: AppCommandContext, message: Message) -> None:
    await ctx.send(f"Quoted message: {message.content}", ephemeral=True)


client.app_command_handler.add_command(user_info)
client.app_command_handler.add_command(quote)


async def main() -> None:
    await client.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
