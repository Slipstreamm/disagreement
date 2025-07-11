# Using Message Components

This guide explains how to work with the `disagreement` message component models. These examples are up to date with the current code base.

## Enabling the New Component System

Messages that use the component system must include the flag `IS_COMPONENTS_V2` (value `1 << 15`). Once this flag is set on a message it cannot be removed.

## Component Categories

The library exposes three broad categories of components:

- **Layout Components** – organize the placement of other components.
- **Content Components** – display static text or media.
- **Interactive Components** – allow the user to interact with your message.

## Action Row

`ActionRow` is a layout container. It may hold up to five buttons or a single select menu.

```python
from disagreement import ActionRow, Button, ButtonStyle

row = ActionRow(components=[
    Button(style=ButtonStyle.PRIMARY, label="Click", custom_id="btn")
])
```

## Button

Buttons provide a clickable UI element.

```python
from disagreement import Button, ButtonStyle

button = Button(
    style=ButtonStyle.SUCCESS,
    label="Confirm",
    custom_id="confirm_button",
)
```

## Select Menus

`SelectMenu` lets the user choose one or more options. The `type` parameter controls the menu variety (`STRING_SELECT`, `USER_SELECT`, `ROLE_SELECT`, `MENTIONABLE_SELECT`, `CHANNEL_SELECT`).

```python
from disagreement import SelectMenu, SelectOption, ComponentType, ChannelType

menu = SelectMenu(
    custom_id="example",
    options=[
        SelectOption(label="Option 1", value="1"),
        SelectOption(label="Option 2", value="2"),
    ],
    placeholder="Choose an option",
    min_values=1,
    max_values=1,
    type=ComponentType.STRING_SELECT,
)
```

For channel selects you may pass `channel_types` with a list of allowed `ChannelType` values.

## Section

`Section` groups one or more `TextDisplay` components and can include an accessory `Button` or `Thumbnail`.

```python
from disagreement import Section, TextDisplay, Thumbnail, UnfurledMediaItem

section = Section(
    components=[
        TextDisplay(content="## Section Title"),
        TextDisplay(content="Sections can hold multiple text displays."),
    ],
    accessory=Thumbnail(media=UnfurledMediaItem(url="https://example.com/img.png")),
)
```

## Text Display

`TextDisplay` simply renders markdown text.

```python
from disagreement import TextDisplay

text_display = TextDisplay(content="**Bold text**")
```

## Thumbnail

`Thumbnail` shows a small image. Set `spoiler=True` to hide the image until clicked.

```python
from disagreement import Thumbnail, UnfurledMediaItem

thumb = Thumbnail(
    media=UnfurledMediaItem(url="https://example.com/image.png"),
    description="A picture",
    spoiler=False,
)
```

## Media Gallery

`MediaGallery` holds multiple `MediaGalleryItem` objects.

```python
from disagreement import MediaGallery, MediaGalleryItem, UnfurledMediaItem

gallery = MediaGallery(
    items=[
        MediaGalleryItem(media=UnfurledMediaItem(url="https://example.com/1.png")),
        MediaGalleryItem(media=UnfurledMediaItem(url="https://example.com/2.png")),
    ]
)
```

## File

`File` displays an uploaded file. Use `spoiler=True` to mark it as a spoiler.

```python
from disagreement import File, UnfurledMediaItem

file_component = File(
    file=UnfurledMediaItem(url="attachment://file.zip"),
    spoiler=False,
)
```

## Separator

`Separator` adds vertical spacing or an optional divider line between components.

```python
from disagreement import Separator

separator = Separator(divider=True, spacing=2)
```

## Container

`Container` visually groups a set of components and can apply an accent colour or spoiler.

```python
from disagreement import Container, TextDisplay

container = Container(
    components=[TextDisplay(content="Inside a container")],
    accent_color="#FF0000",  # int or Color() also work
    spoiler=False,
)
```

A container can itself contain layout and content components, letting you build complex messages.


## Persistent Views

Views with ``timeout=None`` are persistent. Their ``custom_id`` components are saved to ``persistent_views.json`` so they survive bot restarts.

```python
class MyView(View):
    @button(label="Press", custom_id="press")
    async def handle(self, view, inter):
        await inter.respond("Pressed!")

client.add_persistent_view(MyView())
```

When the client starts, it loads this file and registers each view again. Remove
the file to clear stored views.

## Next Steps

- [Slash Commands](slash_commands.md)
- [Caching](caching.md)
- [Voice Features](voice_features.md)
- [HTTP Client Options](http_client.md)

