"""Example showing how to present a modal using a slash command."""

import os
import asyncio

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - example helper
    load_dotenv = None
    print("python-dotenv is not installed. Environment variables will not be loaded")

from disagreement import Client, ui, GatewayIntent
from disagreement.enums import TextInputStyle
from disagreement.ext.app_commands import slash_command, AppCommandContext

if load_dotenv:
    load_dotenv()

token = os.getenv("DISCORD_BOT_TOKEN", "")
application_id = os.getenv("DISCORD_APPLICATION_ID", "")

client = Client(
    token=token, application_id=application_id, intents=GatewayIntent.default()
)


class FeedbackModal(ui.Modal):
    def __init__(self) -> None:
        super().__init__(title="Feedback", custom_id="feedback")

    @ui.text_input(label="Your feedback", style=TextInputStyle.PARAGRAPH)
    async def feedback(self, interaction):
        await interaction.respond(content="Thanks for your feedback!", ephemeral=True)


@slash_command(name="feedback", description="Send feedback via a modal")
async def feedback_command(ctx: AppCommandContext):
    await ctx.interaction.respond_modal(FeedbackModal())


client.app_command_handler.add_command(feedback_command)


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


async def main():
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
