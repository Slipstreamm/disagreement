"""Example showing how to send a modal."""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from disagreement import Client, GatewayIntent, ui  # type: ignore
from disagreement.ext.app_commands.decorators import slash_command
from disagreement.ext.app_commands.context import AppCommandContext

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
APP_ID = os.getenv("DISCORD_APPLICATION_ID", "")

if not TOKEN:
    print("DISCORD_BOT_TOKEN not set")
    sys.exit(1)

client = Client(token=TOKEN, intents=GatewayIntent.default(), application_id=APP_ID)


class NameModal(ui.Modal):
    def __init__(self):
        super().__init__(title="Your Name", custom_id="name_modal")
        self.name = ui.TextInput(label="Name", custom_id="name")


@slash_command(name="namemodal", description="Shows a modal")
async def _namemodal(ctx: AppCommandContext):
    await ctx.interaction.response.send_modal(NameModal())


client.app_command_handler.add_command(_namemodal)


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


if __name__ == "__main__":
    import asyncio

    asyncio.run(client.run())
