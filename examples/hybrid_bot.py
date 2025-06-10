import asyncio
import os
import logging
from typing import Any, Optional, Literal, Union

from disagreement import HybridContext

from disagreement.client import Client
from disagreement.ext.commands.cog import Cog
from disagreement.ext.commands.core import CommandContext
from disagreement.ext.app_commands.decorators import (
    slash_command,
    user_command,
    message_command,
    hybrid_command,
)
from disagreement.ext.app_commands.commands import (
    AppCommandGroup,
)  # For defining groups
from disagreement.ext.app_commands.context import AppCommandContext  # Added
from disagreement.models import (
    User,
    Member,
    Role,
    Attachment,
    Message,
    Channel,
)  # For type hints
from disagreement.enums import (
    ChannelType,
)  # For channel option type hints, assuming it exists

# from disagreement.interactions import Interaction # Replaced by AppCommandContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()


# --- Define a Test Cog ---
class TestCog(Cog):
    def __init__(self, client: Client):
        super().__init__(client)

    @slash_command(name="greet", description="Sends a greeting.")
    async def greet_slash(self, ctx: AppCommandContext, name: str):
        await ctx.send(f"Hello, {name}! (Slash)")

    @user_command(name="Show User Info")
    async def show_user_info_user(
        self, ctx: AppCommandContext, user: User
    ):  # Target user is in ctx.interaction.data.target_id and resolved
        target_user = (
            ctx.interaction.data.resolved.users.get(ctx.interaction.data.target_id)
            if ctx.interaction.data
            and ctx.interaction.data.resolved
            and ctx.interaction.data.target_id
            else user
        )
        if target_user:
            await ctx.send(
                f"User: {target_user.username}#{target_user.discriminator} (ID: {target_user.id}) (User Cmd)",
                ephemeral=True,
            )
        else:
            await ctx.send("Could not find user information.", ephemeral=True)

    @message_command(name="Quote Message")
    async def quote_message_msg(
        self, ctx: AppCommandContext, message: Message
    ):  # Target message is in ctx.interaction.data.target_id and resolved
        target_message = (
            ctx.interaction.data.resolved.messages.get(ctx.interaction.data.target_id)
            if ctx.interaction.data
            and ctx.interaction.data.resolved
            and ctx.interaction.data.target_id
            else message
        )
        if target_message:
            await ctx.send(
                f'Quoting {target_message.author.username}: "{target_message.content}" (Message Cmd)',
                ephemeral=True,
            )
        else:
            await ctx.send("Could not find message to quote.", ephemeral=True)

    @hybrid_command(name="ping", description="Checks bot latency.", aliases=["pong"])
    async def ping_hybrid(
        self, ctx: Union[CommandContext, AppCommandContext], arg: Optional[str] = None
    ):
        latency = self.client.latency
        latency_ms = f"{latency * 1000:.0f}" if latency is not None else "N/A"
        hybrid = HybridContext(ctx)
        await hybrid.send(f"Pong! {latency_ms}ms. Arg: {arg} (Hybrid)")

    @slash_command(name="options_test", description="Tests various option types.")
    async def options_test_slash(
        self,
        ctx: AppCommandContext,
        text: str,
        integer: int,
        boolean: bool,
        number: float,
        user_option: User,
        role_option: Role,
        attachment_option: Attachment,
        choice_option_str: Literal["apple", "banana", "cherry"],
        # Channel and member options as well as numeric Literal choices are
        # not yet exercised in tests pending full library support.
    ):
        response_parts = [
            f"Text: {text}",
            f"Integer: {integer}",
            f"Boolean: {boolean}",
            f"Number: {number}",
            f"User: {user_option.username}#{user_option.discriminator}",
            f"Role: {role_option.name}",
            f"Attachment: {attachment_option.filename} (URL: {attachment_option.url})",
            f"Choice Str: {choice_option_str}",
        ]
        await ctx.send("\n".join(response_parts), ephemeral=True)

    # --- Subcommand Group Test ---
    # Define the group as a class attribute.
    # The AppCommandHandler's discovery mechanism (via Cog) should pick up AppCommandGroup instances.
    settings_group = AppCommandGroup(
        name="settings",
        description="Manage bot settings.",
        # guild_ids can be added here if the group is guild-specific
    )

    @slash_command(
        name="show", description="Shows current setting values.", parent=settings_group
    )
    async def settings_show(
        self, ctx: AppCommandContext, setting_name: Optional[str] = None
    ):
        if setting_name:
            await ctx.send(
                f"Showing value for setting: {setting_name} (Value: Placeholder)",
                ephemeral=True,
            )
        else:
            await ctx.send(
                "Showing all settings: (Placeholder for all settings)", ephemeral=True
            )

    @slash_command(
        name="update", description="Updates a setting.", parent=settings_group
    )
    async def settings_update(
        self, ctx: AppCommandContext, setting_name: str, value: str
    ):
        await ctx.send(
            f"Updated setting: {setting_name} to value: {value}", ephemeral=True
        )

    # The Cog's metaclass or command registration logic should handle adding `settings_group`
    # (and its subcommands) to the client's AppCommandHandler.
    # The decorators now handle associating subcommands with their parent group.

    @slash_command(
        name="numeric_choices_test", description="Tests integer and float choices."
    )
    async def numeric_choices_test_slash(
        self,
        ctx: AppCommandContext,
        int_choice: Literal[10, 20, 30, 42],
        float_choice: float,
    ):
        response = (
            f"Integer Choice: {int_choice} (Type: {type(int_choice).__name__})\n"
            f"Float Choice: {float_choice} (Type: {type(float_choice).__name__})"
        )
        await ctx.send(response, ephemeral=True)

    @slash_command(
        name="numeric_choices_extended",
        description="Tests additional integer and float choice handling.",
    )
    async def numeric_choices_extended_slash(
        self,
        ctx: AppCommandContext,
        int_choice: Literal[-5, 0, 5],
        float_choice: float,
    ):
        response = (
            f"Int Choice: {int_choice} (Type: {type(int_choice).__name__})\n"
            f"Float Choice: {float_choice} (Type: {type(float_choice).__name__})"
        )
        await ctx.send(response, ephemeral=True)

    @slash_command(
        name="channel_member_test",
        description="Tests channel and member options.",
    )
    async def channel_member_test_slash(
        self,
        ctx: AppCommandContext,
        channel: Channel,
        member: Member,
    ):
        response = (
            f"Channel: {channel.name} (Type: {channel.type.name})\n"
            f"Member: {member.username}#{member.discriminator}"
        )
        await ctx.send(response, ephemeral=True)

    @slash_command(
        name="channel_types_test",
        description="Demonstrates multiple channel type options.",
    )
    async def channel_types_test_slash(
        self,
        ctx: AppCommandContext,
        text_channel: Channel,
        voice_channel: Channel,
        category_channel: Channel,
    ):
        response = (
            f"Text: {text_channel.type.name}\n"
            f"Voice: {voice_channel.type.name}\n"
            f"Category: {category_channel.type.name}"
        )
        await ctx.send(response, ephemeral=True)


# --- Main Bot Script ---
async def main():
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    application_id = os.getenv("DISCORD_APPLICATION_ID")

    if not bot_token:
        logger.error("Error: DISCORD_BOT_TOKEN environment variable not set.")
        return
    if not application_id:
        logger.error("Error: DISCORD_APPLICATION_ID environment variable not set.")
        return

    client = Client(token=bot_token, command_prefix="!", application_id=application_id)

    @client.event
    async def on_ready():
        if client.user:
            logger.info(
                f"Bot logged in as {client.user.username}#{client.user.discriminator}"
            )
        else:
            logger.error(
                "Client ready, but client.user is not populated! This should not happen."
            )
            return  # Avoid proceeding if basic client info isn't there

        if client.application_id:
            logger.info(f"Application ID is: {client.application_id}")
            # Sync application commands (global in this case)
            try:
                logger.info("Attempting to sync application commands...")
                # Ensure application_id is not None before passing
                app_id_to_sync = client.application_id
                if (
                    app_id_to_sync is not None
                ):  # Redundant due to outer if, but good for clarity
                    await client.app_command_handler.sync_commands(
                        application_id=app_id_to_sync
                    )
                    logger.info("Application commands synced successfully.")
                else:  # Should not be reached if outer if client.application_id is true
                    logger.error(
                        "Application ID was None despite initial check. Skipping sync."
                    )
            except Exception as e:
                logger.error(f"Error syncing application commands: {e}", exc_info=True)
        else:
            # This case should be less likely now that Client gets it from READY.
            # If DISCORD_APPLICATION_ID was critical as a fallback, that logic would be here.
            # For now, we rely on the READY event.
            logger.warning(
                "Client's application ID is not set after READY. Skipping application command sync."
            )
            # Check if the environment variable was provided, as a diagnostic.
            if not application_id:
                logger.warning(
                    "DISCORD_APPLICATION_ID environment variable was also not provided."
                )

    client.add_cog(TestCog(client))

    try:
        await client.run()
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
    except Exception as e:
        logger.error(
            f"An error occurred in the bot's main run loop: {e}", exc_info=True
        )
    finally:
        if not client.is_closed():
            await client.close()
        logger.info("Bot has been closed.")


if __name__ == "__main__":
    # For Windows, to allow graceful shutdown with Ctrl+C
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Main loop interrupted. Exiting.")
