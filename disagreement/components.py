"""Message component utilities."""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from .enums import ComponentType, ButtonStyle, ChannelType, TextInputStyle
from .models import (
    ActionRow,
    Button,
    Component,
    SelectMenu,
    SelectOption,
    PartialEmoji,
    PartialEmoji,
    Section,
    TextDisplay,
    Thumbnail,
    MediaGallery,
    MediaGalleryItem,
    FileComponent,
    Separator,
    Container,
    UnfurledMediaItem,
)

if TYPE_CHECKING:  # pragma: no cover - optional client for future use
    from .client import Client


def component_factory(
    data: Dict[str, Any], client: Optional["Client"] = None
) -> "Component":
    """Create a component object from raw API data."""
    ctype = ComponentType(data["type"])

    if ctype == ComponentType.ACTION_ROW:
        row = ActionRow()
        for comp in data.get("components", []):
            row.add_component(component_factory(comp, client))
        return row

    if ctype == ComponentType.BUTTON:
        return Button(
            style=ButtonStyle(data["style"]),
            label=data.get("label"),
            emoji=PartialEmoji(data["emoji"]) if data.get("emoji") else None,
            custom_id=data.get("custom_id"),
            url=data.get("url"),
            disabled=data.get("disabled", False),
        )

    if ctype in {
        ComponentType.STRING_SELECT,
        ComponentType.USER_SELECT,
        ComponentType.ROLE_SELECT,
        ComponentType.MENTIONABLE_SELECT,
        ComponentType.CHANNEL_SELECT,
    }:
        options = [
            SelectOption(
                label=o["label"],
                value=o["value"],
                description=o.get("description"),
                emoji=PartialEmoji(o["emoji"]) if o.get("emoji") else None,
                default=o.get("default", False),
            )
            for o in data.get("options", [])
        ]
        channel_types = None
        if ctype == ComponentType.CHANNEL_SELECT and data.get("channel_types"):
            channel_types = [ChannelType(ct) for ct in data.get("channel_types", [])]

        return SelectMenu(
            custom_id=data["custom_id"],
            options=options,
            placeholder=data.get("placeholder"),
            min_values=data.get("min_values", 1),
            max_values=data.get("max_values", 1),
            disabled=data.get("disabled", False),
            channel_types=channel_types,
            type=ctype,
        )

    if ctype == ComponentType.TEXT_INPUT:
        from .ui.modal import TextInput

        return TextInput(
            label=data.get("label", ""),
            custom_id=data.get("custom_id"),
            style=TextInputStyle(data.get("style", TextInputStyle.SHORT.value)),
            placeholder=data.get("placeholder"),
            required=data.get("required", True),
            min_length=data.get("min_length"),
            max_length=data.get("max_length"),
        )

    if ctype == ComponentType.SECTION:
        # The components in a section can only be TextDisplay
        section_components = []
        for c in data.get("components", []):
            comp = component_factory(c, client)
            if isinstance(comp, TextDisplay):
                section_components.append(comp)

        accessory = None
        if data.get("accessory"):
            acc_comp = component_factory(data["accessory"], client)
            if isinstance(acc_comp, (Thumbnail, Button)):
                accessory = acc_comp

        return Section(
            components=section_components,
            accessory=accessory,
            id=data.get("id"),
        )

    if ctype == ComponentType.TEXT_DISPLAY:
        return TextDisplay(content=data["content"], id=data.get("id"))

    if ctype == ComponentType.THUMBNAIL:
        return Thumbnail(
            media=UnfurledMediaItem(**data["media"]),
            description=data.get("description"),
            spoiler=data.get("spoiler", False),
            id=data.get("id"),
        )

    if ctype == ComponentType.MEDIA_GALLERY:
        return MediaGallery(
            items=[
                MediaGalleryItem(
                    media=UnfurledMediaItem(**i["media"]),
                    description=i.get("description"),
                    spoiler=i.get("spoiler", False),
                )
                for i in data.get("items", [])
            ],
            id=data.get("id"),
        )

    if ctype == ComponentType.FILE:
        return FileComponent(
            file=UnfurledMediaItem(**data["file"]),
            spoiler=data.get("spoiler", False),
            id=data.get("id"),
        )

    if ctype == ComponentType.SEPARATOR:
        return Separator(
            divider=data.get("divider", True),
            spacing=data.get("spacing", 1),
            id=data.get("id"),
        )

    if ctype == ComponentType.CONTAINER:
        return Container(
            components=[
                component_factory(c, client) for c in data.get("components", [])
            ],
            accent_color=data.get("accent_color"),
            spoiler=data.get("spoiler", False),
            id=data.get("id"),
        )

    raise ValueError(f"Unsupported component type: {ctype}")
