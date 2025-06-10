import os
import asyncio
from typing import Union, Optional
from disagreement import Client, ui, HybridContext
from disagreement.models import (
    Message,
    SelectOption,
    User,
    Member,
    Role,
    Attachment,
    Channel,
    ActionRow,
    Button,
    Section,
    TextDisplay,
    Thumbnail,
    UnfurledMediaItem,
    MediaGallery,
    MediaGalleryItem,
    Container,
)
from disagreement.enums import (
    ButtonStyle,
    GatewayIntent,
    ChannelType,
    MessageFlags,
    InteractionCallbackType,
    MessageFlags,
)
from disagreement.ext.commands.cog import Cog
from disagreement.ext.commands.core import CommandContext
from disagreement.ext.app_commands.decorators import hybrid_command, slash_command
from disagreement.ext.app_commands.context import AppCommandContext
from disagreement.interactions import (
    Interaction,
    InteractionResponsePayload,
    InteractionCallbackData,
)
from dotenv import load_dotenv

load_dotenv()

# Get the bot token and application ID from the environment variables
token = os.getenv("DISCORD_BOT_TOKEN")
application_id = os.getenv("DISCORD_APPLICATION_ID")

if not token:
    raise ValueError("Bot token not found in environment variables")
if not application_id:
    raise ValueError("Application ID not found in environment variables")

# Define the intents
intents = GatewayIntent.default() | GatewayIntent.MESSAGE_CONTENT

# Create a new client
client = Client(
    token=token,
    intents=intents,
    command_prefix="!",
    mention_replies=True,
)

# Simple stock data used for the stock cycling example
STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "price": "$175"},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "price": "$315"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": "$128"},
]


# Define a View class that contains our components
class MyView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)  # 180-second timeout
        self.click_count = 0

    @ui.button(label="Click Me!", style=ButtonStyle.SUCCESS, emoji="🖱️")
    async def click_me(self, interaction: Interaction):
        self.click_count += 1
        await interaction.respond(
            content=f"You've clicked the button {self.click_count} times!",
            ephemeral=True,
        )

    @ui.select(
        custom_id="string_select",
        placeholder="Choose an option",
        options=[
            SelectOption(
                label="Option 1", value="opt1", description="This is the first option"
            ),
            SelectOption(
                label="Option 2", value="opt2", description="This is the second option"
            ),
        ],
    )
    async def select_menu(self, interaction: Interaction):
        if interaction.data and interaction.data.values:
            await interaction.respond(
                content=f"You selected: {interaction.data.values[0]}",
                ephemeral=True,
            )

    async def on_timeout(self):
        # This method is called when the view times out.
        # You can use this to edit the original message, for example.
        print("View has timed out!")


# View for cycling through available stocks
class StockView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.index = 0

    @ui.button(label="Next Stock", style=ButtonStyle.PRIMARY)
    async def next_stock(self, interaction: Interaction):
        self.index = (self.index + 1) % len(STOCKS)
        stock = STOCKS[self.index]
        # Edit the message by responding to the interaction with an update
        await interaction.edit(
            content=f"**{stock['symbol']}** - {stock['name']}\nPrice: {stock['price']}",
            components=self.to_components(),
            # Preserve the original reply mention
            allowed_mentions={"replied_user": True},
        )


class ComponentCommandsCog(Cog):
    def __init__(self, client: Client):
        super().__init__(client)

    @hybrid_command(name="components", description="Sends interactive components.")
    async def components_command(self, ctx: Union[CommandContext, AppCommandContext]):
        # Send a message with the view using a hybrid context helper
        hybrid = HybridContext(ctx)
        await hybrid.send("Here are your components:", view=MyView())

    @hybrid_command(
        name="stocks", description="Shows stock information with navigation."
    )
    async def stocks_command(self, ctx: Union[CommandContext, AppCommandContext]):
        # Show the first stock and attach a button to cycle through them
        first = STOCKS[0]
        hybrid = HybridContext(ctx)
        await hybrid.send(
            f"**{first['symbol']}** - {first['name']}\nPrice: {first['price']}",
            view=StockView(),
        )

    @hybrid_command(name="sectiondemo", description="Shows a section layout.")
    async def section_demo(self, ctx: Union[CommandContext, AppCommandContext]) -> None:
        section = Section(
            components=[
                TextDisplay(content="## Advanced Components"),
                TextDisplay(content="Sections group text with accessories."),
            ],
            accessory=Thumbnail(
                media=UnfurledMediaItem(url="https://placehold.co/100x100.png")
            ),
        )
        container = Container(components=[section], accent_color=0x5865F2)
        hybrid = HybridContext(ctx)
        await hybrid.send(
            components=[container],
            flags=MessageFlags.IS_COMPONENTS_V2.value,
        )

    @hybrid_command(name="gallerydemo", description="Shows a media gallery.")
    async def gallery_demo(self, ctx: Union[CommandContext, AppCommandContext]) -> None:
        gallery = MediaGallery(
            items=[
                MediaGalleryItem(
                    media=UnfurledMediaItem(url="https://placehold.co/600x400.png")
                ),
                MediaGalleryItem(
                    media=UnfurledMediaItem(url="https://placehold.co/600x400.jpg")
                ),
            ]
        )
        hybrid = HybridContext(ctx)
        await hybrid.send(
            components=[gallery],
            flags=MessageFlags.IS_COMPONENTS_V2.value,
        )

    @hybrid_command(
        name="complex_components",
        description="Shows a complex layout with multiple containers.",
    )
    async def complex_components(
        self, ctx: Union[CommandContext, AppCommandContext]
    ) -> None:
        container1 = Container(
            components=[
                Section(
                    components=[
                        TextDisplay(content="## Complex Layout Example"),
                        TextDisplay(
                            content="This container has an accent color and includes a section with an action row of buttons. There is a thumbnail accessory to the right."
                        ),
                    ],
                    accessory=Thumbnail(
                        media=UnfurledMediaItem(url="https://placehold.co/100x100.png")
                    ),
                ),
                ActionRow(
                    components=[
                        Button(
                            style=ButtonStyle.PRIMARY,
                            label="Primary",
                            custom_id="complex_primary",
                        ),
                        Button(
                            style=ButtonStyle.SUCCESS,
                            label="Success",
                            custom_id="complex_success",
                        ),
                        Button(
                            style=ButtonStyle.DANGER,
                            label="Destructive",
                            custom_id="complex_destructive",
                        ),
                    ]
                ),
            ],
            accent_color=0x5865F2,
        )
        container2 = Container(
            components=[
                TextDisplay(
                    content="## Another Container\nThis container has no accent color and includes a media gallery."
                ),
                MediaGallery(
                    items=[
                        MediaGalleryItem(
                            media=UnfurledMediaItem(
                                url="https://placehold.co/300x200.png"
                            )
                        ),
                        MediaGalleryItem(
                            media=UnfurledMediaItem(
                                url="https://placehold.co/300x200.jpg"
                            )
                        ),
                        MediaGalleryItem(
                            media=UnfurledMediaItem(
                                url="https://placehold.co/300x200.gif"
                            )
                        ),
                    ]
                ),
            ]
        )

        hybrid = HybridContext(ctx)
        await hybrid.send(
            components=[container1, container2],
            flags=MessageFlags.IS_COMPONENTS_V2.value,
        )


async def main():
    @client.event
    async def on_ready():
        if client.user:
            print(f"Logged in as {client.user.username}")
            if client.application_id:
                try:
                    print("Attempting to sync application commands...")
                    await client.app_command_handler.sync_commands(
                        application_id=client.application_id
                    )
                    print("Application commands synced successfully.")
                except Exception as e:
                    print(f"Error syncing application commands: {e}")
            else:
                print(
                    "Client's application ID is not set. Skipping application command sync."
                )

    client.add_cog(ComponentCommandsCog(client))
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
