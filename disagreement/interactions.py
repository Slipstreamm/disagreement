# disagreement/interactions.py

"""
Data models for Discord Interaction objects.
"""

from typing import Optional, List, Dict, Union, Any, TYPE_CHECKING

from .enums import (
    ApplicationCommandType,
    ApplicationCommandOptionType,
    InteractionType,
    InteractionCallbackType,
    IntegrationType,
    InteractionContextType,
    ChannelType,
)

# Runtime imports for models used in this module
from .models import (
    User,
    Message,
    Member,
    Role,
    Embed,
    PartialChannel,
    Attachment,
    ActionRow,
    Component,
    AllowedMentions,
)

if TYPE_CHECKING:
    # Import Client type only for type checking to avoid circular imports
    from .client import Client
    from .ui.modal import Modal

    # MessageFlags, PartialAttachment can be added if/when defined

Snowflake = str


# Based on Application Command Option Choice Structure
class ApplicationCommandOptionChoice:
    """Represents a choice for an application command option."""

    def __init__(self, data: dict):
        self.name: str = data["name"]
        self.value: Union[str, int, float] = data["value"]
        self.name_localizations: Optional[Dict[str, str]] = data.get(
            "name_localizations"
        )

    def __repr__(self) -> str:
        return (
            f"<ApplicationCommandOptionChoice name='{self.name}' value={self.value!r}>"
        )

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"name": self.name, "value": self.value}
        if self.name_localizations:
            payload["name_localizations"] = self.name_localizations
        return payload


# Based on Application Command Option Structure
class ApplicationCommandOption:
    """Represents an option for an application command."""

    def __init__(self, data: dict):
        self.type: ApplicationCommandOptionType = ApplicationCommandOptionType(
            data["type"]
        )
        self.name: str = data["name"]
        self.description: str = data["description"]
        self.required: bool = data.get("required", False)

        self.choices: Optional[List[ApplicationCommandOptionChoice]] = (
            [ApplicationCommandOptionChoice(c) for c in data["choices"]]
            if data.get("choices")
            else None
        )

        self.options: Optional[List["ApplicationCommandOption"]] = (
            [ApplicationCommandOption(o) for o in data["options"]]
            if data.get("options")
            else None
        )  # For subcommands/groups

        self.channel_types: Optional[List[ChannelType]] = (
            [ChannelType(ct) for ct in data.get("channel_types", [])]
            if data.get("channel_types")
            else None
        )
        self.min_value: Optional[Union[int, float]] = data.get("min_value")
        self.max_value: Optional[Union[int, float]] = data.get("max_value")
        self.min_length: Optional[int] = data.get("min_length")
        self.max_length: Optional[int] = data.get("max_length")
        self.autocomplete: bool = data.get("autocomplete", False)
        self.name_localizations: Optional[Dict[str, str]] = data.get(
            "name_localizations"
        )
        self.description_localizations: Optional[Dict[str, str]] = data.get(
            "description_localizations"
        )

    def __repr__(self) -> str:
        return f"<ApplicationCommandOption name='{self.name}' type={self.type!r}>"

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
        }
        if self.required:  # Defaults to False, only include if True
            payload["required"] = self.required
        if self.choices:
            payload["choices"] = [c.to_dict() for c in self.choices]
        if self.options:  # For subcommands/groups
            payload["options"] = [o.to_dict() for o in self.options]
        if self.channel_types:
            payload["channel_types"] = [ct.value for ct in self.channel_types]
        if self.min_value is not None:
            payload["min_value"] = self.min_value
        if self.max_value is not None:
            payload["max_value"] = self.max_value
        if self.min_length is not None:
            payload["min_length"] = self.min_length
        if self.max_length is not None:
            payload["max_length"] = self.max_length
        if self.autocomplete:  # Defaults to False, only include if True
            payload["autocomplete"] = self.autocomplete
        if self.name_localizations:
            payload["name_localizations"] = self.name_localizations
        if self.description_localizations:
            payload["description_localizations"] = self.description_localizations
        return payload


# Based on Application Command Structure
class ApplicationCommand:
    """Represents an application command."""

    def __init__(self, data: dict):
        self.id: Optional[Snowflake] = data.get("id")
        self.type: ApplicationCommandType = ApplicationCommandType(
            data.get("type", 1)
        )  # Default to CHAT_INPUT
        self.application_id: Optional[Snowflake] = data.get("application_id")
        self.guild_id: Optional[Snowflake] = data.get("guild_id")
        self.name: str = data["name"]
        self.description: str = data.get(
            "description", ""
        )  # Empty for USER/MESSAGE commands

        self.options: Optional[List[ApplicationCommandOption]] = (
            [ApplicationCommandOption(o) for o in data["options"]]
            if data.get("options")
            else None
        )

        self.default_member_permissions: Optional[str] = data.get(
            "default_member_permissions"
        )
        self.dm_permission: Optional[bool] = data.get("dm_permission")  # Deprecated
        self.nsfw: bool = data.get("nsfw", False)
        self.version: Optional[Snowflake] = data.get("version")
        self.name_localizations: Optional[Dict[str, str]] = data.get(
            "name_localizations"
        )
        self.description_localizations: Optional[Dict[str, str]] = data.get(
            "description_localizations"
        )

        self.integration_types: Optional[List[IntegrationType]] = (
            [IntegrationType(it) for it in data["integration_types"]]
            if data.get("integration_types")
            else None
        )

        self.contexts: Optional[List[InteractionContextType]] = (
            [InteractionContextType(c) for c in data["contexts"]]
            if data.get("contexts")
            else None
        )

    def __repr__(self) -> str:
        return (
            f"<ApplicationCommand id='{self.id}' name='{self.name}' type={self.type!r}>"
        )


# Based on Interaction Object's Resolved Data Structure
class ResolvedData:
    """Represents resolved data for an interaction."""

    def __init__(
        self, data: dict, client_instance: Optional["Client"] = None
    ):  # client_instance for model hydration
        # Models are now imported in TYPE_CHECKING block

        users_data = data.get("users", {})
        self.users: Dict[Snowflake, "User"] = {
            uid: User(udata) for uid, udata in users_data.items()
        }

        self.members: Dict[Snowflake, "Member"] = {}
        for mid, mdata in data.get("members", {}).items():
            member_payload = dict(mdata)
            member_payload.setdefault("id", mid)
            if "user" not in member_payload and mid in users_data:
                member_payload["user"] = users_data[mid]
            self.members[mid] = Member(member_payload, client_instance=client_instance)

        self.roles: Dict[Snowflake, "Role"] = {
            rid: Role(rdata) for rid, rdata in data.get("roles", {}).items()
        }

        self.channels: Dict[Snowflake, "PartialChannel"] = {
            cid: PartialChannel(cdata, client_instance=client_instance)
            for cid, cdata in data.get("channels", {}).items()
        }

        self.messages: Dict[Snowflake, "Message"] = (
            {
                mid: Message(mdata, client_instance=client_instance) for mid, mdata in data.get("messages", {}).items()  # type: ignore[misc]
            }
            if client_instance
            else {}
        )  # Only hydrate if client is available

        self.attachments: Dict[Snowflake, "Attachment"] = {
            aid: Attachment(adata) for aid, adata in data.get("attachments", {}).items()
        }

    def __repr__(self) -> str:
        return f"<ResolvedData users={len(self.users)} members={len(self.members)} roles={len(self.roles)} channels={len(self.channels)} messages={len(self.messages)} attachments={len(self.attachments)}>"


# Based on Interaction Object's Data Structure (for Application Commands)
class InteractionData:
    """Represents the data payload for an interaction."""

    def __init__(self, data: dict, client_instance: Optional["Client"] = None):
        self.id: Optional[Snowflake] = data.get("id")  # Command ID
        self.name: Optional[str] = data.get("name")  # Command name
        self.type: Optional[ApplicationCommandType] = (
            ApplicationCommandType(data["type"]) if data.get("type") else None
        )

        self.resolved: Optional[ResolvedData] = (
            ResolvedData(data["resolved"], client_instance=client_instance)
            if data.get("resolved")
            else None
        )

        # For CHAT_INPUT, this is List[ApplicationCommandInteractionDataOption]
        # For USER/MESSAGE, this is not present or different.
        # For now, storing as raw list of dicts. Parsing can happen in handler.
        self.options: Optional[List[Dict[str, Any]]] = data.get("options")

        # For message components
        self.custom_id: Optional[str] = data.get("custom_id")
        self.component_type: Optional[int] = data.get("component_type")
        self.values: Optional[List[str]] = data.get("values")

        self.guild_id: Optional[Snowflake] = data.get("guild_id")
        self.target_id: Optional[Snowflake] = data.get(
            "target_id"
        )  # For USER/MESSAGE commands

    def __repr__(self) -> str:
        return f"<InteractionData id='{self.id}' name='{self.name}' type={self.type!r}>"


# Based on Interaction Object Structure
class Interaction:
    """Represents an interaction from Discord."""

    def __init__(self, data: dict, client_instance: "Client"):
        self._client: "Client" = client_instance

        self.id: Snowflake = data["id"]
        self.application_id: Snowflake = data["application_id"]
        self.type: InteractionType = InteractionType(data["type"])

        self.data: Optional[InteractionData] = (
            InteractionData(data["data"], client_instance=client_instance)
            if data.get("data")
            else None
        )

        self.guild_id: Optional[Snowflake] = data.get("guild_id")
        self.channel_id: Optional[Snowflake] = data.get(
            "channel_id"
        )  # Will be present on command invocations

        member_data = data.get("member")
        user_data_from_member = (
            member_data.get("user") if isinstance(member_data, dict) else None
        )

        self.member: Optional["Member"] = (
            Member(member_data, client_instance=self._client) if member_data else None
        )

        # User object is included within member if in guild, otherwise it's top-level
        # If self.member was successfully hydrated, its .user attribute should be preferred if it exists.
        # However, Member.__init__ handles setting User attributes.
        # The primary source for User is data.get("user") or member_data.get("user").

        if data.get("user"):
            self.user: Optional["User"] = User(data["user"])
        elif user_data_from_member:
            self.user: Optional["User"] = User(user_data_from_member)
        elif (
            self.member
        ):  # If member was hydrated and has user attributes (e.g. from Member(User) inheritance)
            # This assumes Member correctly populates its User parts.
            self.user: Optional["User"] = self.member  # Member is a User subclass
        else:
            self.user: Optional["User"] = None

        self.token: str = data["token"]  # For responding to the interaction
        self.version: int = data["version"]

        self.message: Optional["Message"] = (
            Message(data["message"], client_instance=client_instance)
            if data.get("message")
            else None
        )  # For component interactions

        self.app_permissions: Optional[str] = data.get(
            "app_permissions"
        )  # Bitwise set of permissions the app has in the source channel
        self.locale: Optional[str] = data.get(
            "locale"
        )  # Selected language of the invoking user
        self.guild_locale: Optional[str] = data.get(
            "guild_locale"
        )  # Guild's preferred language

        self.response = InteractionResponse(self)

    async def respond(
        self,
        content: Optional[str] = None,
        *,
        embed: Optional[Embed] = None,
        embeds: Optional[List[Embed]] = None,
        components: Optional[List[ActionRow]] = None,
        ephemeral: bool = False,
        tts: bool = False,
    ) -> None:
        """|coro|

        Responds to this interaction.

        Parameters:
            content (Optional[str]): The content of the message.
            embed (Optional[Embed]): A single embed to send.
            embeds (Optional[List[Embed]]): A list of embeds to send.
            components (Optional[List[ActionRow]]): A list of ActionRow components.
            ephemeral (bool): Whether the response should be ephemeral (only visible to the user).
            tts (bool): Whether the message should be sent with text-to-speech.
        """
        if embed and embeds:
            raise ValueError("Cannot provide both embed and embeds.")

        data: Dict[str, Any] = {}
        if tts:
            data["tts"] = True
        if content:
            data["content"] = content
        if embed:
            data["embeds"] = [embed.to_dict()]
        elif embeds:
            data["embeds"] = [e.to_dict() for e in embeds]
        if components:
            data["components"] = [c.to_dict() for c in components]
        if ephemeral:
            data["flags"] = 1 << 6  # EPHEMERAL flag

        payload = InteractionResponsePayload(
            type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
            data=InteractionCallbackData(data),
        )

        await self._client._http.create_interaction_response(
            interaction_id=self.id,
            interaction_token=self.token,
            payload=payload,
        )

    async def respond_modal(self, modal: "Modal") -> None:
        """|coro| Send a modal in response to this interaction."""

        from typing import Any, cast

        payload = {
            "type": InteractionCallbackType.MODAL.value,
            "data": modal.to_dict(),
        }
        await self._client._http.create_interaction_response(
            interaction_id=self.id,
            interaction_token=self.token,
            payload=cast(Any, payload),
        )

    async def edit(
        self,
        content: Optional[str] = None,
        *,
        embed: Optional[Embed] = None,
        embeds: Optional[List[Embed]] = None,
        components: Optional[List[ActionRow]] = None,
        attachments: Optional[List[Any]] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
    ) -> None:
        """|coro|

        Edits the original response to this interaction.

        If the interaction is from a component, this will acknowledge the
        interaction and update the message in one operation.

        Parameters:
            content (Optional[str]): The new message content.
            embed (Optional[Embed]): A single embed to send. Ignored if
                ``embeds`` is provided.
            embeds (Optional[List[Embed]]): A list of embeds to send.
            components (Optional[List[ActionRow]]): Updated components for the
                message.
            attachments (Optional[List[Any]]): Attachments to include with the
                message.
            allowed_mentions (Optional[Dict[str, Any]]): Controls mentions in the
                message.
        """
        if embed and embeds:
            raise ValueError("Cannot provide both embed and embeds.")

        payload_data: Dict[str, Any] = {}
        if content is not None:
            payload_data["content"] = content
        if embed:
            payload_data["embeds"] = [embed.to_dict()]
        elif embeds is not None:
            payload_data["embeds"] = [e.to_dict() for e in embeds]
        if components is not None:
            payload_data["components"] = [c.to_dict() for c in components]
        if attachments is not None:
            payload_data["attachments"] = [
                a.to_dict() if hasattr(a, "to_dict") else a for a in attachments
            ]
        if allowed_mentions is not None:
            payload_data["allowed_mentions"] = allowed_mentions

        if self.type == InteractionType.MESSAGE_COMPONENT:
            # For component interactions, we send an UPDATE_MESSAGE response
            # to acknowledge the interaction and edit the message simultaneously.
            payload = InteractionResponsePayload(
                type=InteractionCallbackType.UPDATE_MESSAGE,
                data=InteractionCallbackData(payload_data),
            )
            await self._client._http.create_interaction_response(
                self.id, self.token, payload
            )
        else:
            # For other interaction types (like an initial slash command response),
            # we edit the original response via the webhook endpoint.
            await self._client._http.edit_original_interaction_response(
                application_id=self.application_id,
                interaction_token=self.token,
                payload=payload_data,
            )

    def __repr__(self) -> str:
        return f"<Interaction id='{self.id}' type={self.type!r}>"


class InteractionResponse:
    """Helper for sending responses for an :class:`Interaction`."""

    def __init__(self, interaction: "Interaction") -> None:
        self._interaction = interaction

    async def send_modal(self, modal: "Modal") -> None:
        """Sends a modal response."""
        payload = InteractionResponsePayload(
            type=InteractionCallbackType.MODAL,
            data=InteractionCallbackData(modal.to_dict()),
        )
        await self._interaction._client._http.create_interaction_response(
            self._interaction.id,
            self._interaction.token,
            payload,
        )


# Based on Interaction Response Object's Data Structure
class InteractionCallbackData:
    """Data for an interaction response."""

    def __init__(self, data: dict):
        self.tts: Optional[bool] = data.get("tts")
        self.content: Optional[str] = data.get("content")
        self.embeds: Optional[List[Embed]] = (
            [Embed(e) for e in data.get("embeds", [])] if data.get("embeds") else None
        )
        self.allowed_mentions: Optional[AllowedMentions] = (
            AllowedMentions(data["allowed_mentions"])
            if data.get("allowed_mentions")
            else None
        )
        self.flags: Optional[int] = data.get("flags")  # MessageFlags enum could be used
        from .components import component_factory

        self.components: Optional[List[Component]] = (
            [component_factory(c) for c in data.get("components", [])]
            if data.get("components")
            else None
        )
        self.attachments: Optional[List[Attachment]] = (
            [Attachment(a) for a in data.get("attachments", [])]
            if data.get("attachments")
            else None
        )

    def to_dict(self) -> dict:
        # Helper to convert to dict for sending to Discord API
        payload = {}
        if self.tts is not None:
            payload["tts"] = self.tts
        if self.content is not None:
            payload["content"] = self.content
        if self.embeds is not None:
            payload["embeds"] = [e.to_dict() for e in self.embeds]
        if self.allowed_mentions is not None:
            payload["allowed_mentions"] = self.allowed_mentions.to_dict()
        if self.flags is not None:
            payload["flags"] = self.flags
        if self.components is not None:
            payload["components"] = [c.to_dict() for c in self.components]
        if self.attachments is not None:
            payload["attachments"] = [a.to_dict() for a in self.attachments]
        return payload

    def __repr__(self) -> str:
        return f"<InteractionCallbackData content='{self.content[:20] if self.content else None}'>"


# Based on Interaction Response Object Structure
class InteractionResponsePayload:
    """Payload for responding to an interaction."""

    def __init__(
        self,
        type: InteractionCallbackType,
        data: Optional[InteractionCallbackData] = None,
    ):
        self.type: InteractionCallbackType = type
        self.data: Optional[InteractionCallbackData] = data

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"type": self.type.value}
        if self.data:
            payload["data"] = self.data.to_dict()
        return payload

    def __repr__(self) -> str:
        return f"<InteractionResponsePayload type={self.type!r}>"
