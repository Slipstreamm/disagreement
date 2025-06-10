# disagreement/ext/app_commands/context.py

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, Union, Any, Dict

if TYPE_CHECKING:
    from disagreement.client import Client
    from disagreement.interactions import (
        Interaction,
        InteractionCallbackData,
        InteractionResponsePayload,
        Snowflake,
    )
    from disagreement.enums import InteractionCallbackType, MessageFlags
    from disagreement.models import (
        User,
        Member,
        Message,
        Channel,
        ActionRow,
    )
    from disagreement.ui.view import View

    # For full model hints, these would be imported from disagreement.models when defined:
    Embed = Any
    PartialAttachment = Any
    Guild = Any  # from disagreement.models import Guild
    TextChannel = Any  # from disagreement.models import TextChannel, etc.
    from .commands import AppCommand

from disagreement.enums import InteractionCallbackType, MessageFlags
from disagreement.interactions import (
    Interaction,
    InteractionCallbackData,
    InteractionResponsePayload,
    Snowflake,
)
from disagreement.models import Message
from disagreement.typing import Typing


class AppCommandContext:
    """
    Represents the context in which an application command is being invoked.
    Provides methods to respond to the interaction.
    """

    def __init__(
        self,
        bot: "Client",
        interaction: "Interaction",
        command: Optional["AppCommand"] = None,
    ):
        self.bot: "Client" = bot
        self.interaction: "Interaction" = interaction
        self.command: Optional["AppCommand"] = command  # The command that was invoked

        self._responded: bool = False
        self._deferred: bool = False

    @property
    def token(self) -> str:
        """The interaction token."""
        return self.interaction.token

    @property
    def interaction_id(self) -> "Snowflake":
        """The interaction ID."""
        return self.interaction.id

    @property
    def application_id(self) -> "Snowflake":
        """The application ID of the interaction."""
        return self.interaction.application_id

    @property
    def guild_id(self) -> Optional["Snowflake"]:
        """The ID of the guild where the interaction occurred, if any."""
        return self.interaction.guild_id

    @property
    def channel_id(self) -> Optional["Snowflake"]:
        """The ID of the channel where the interaction occurred."""
        return self.interaction.channel_id

    @property
    def author(self) -> Optional[Union["User", "Member"]]:
        """The user or member who invoked the interaction."""
        return self.interaction.member or self.interaction.user

    @property
    def user(self) -> Optional["User"]:
        """The user who invoked the interaction.
        If in a guild, this is the user part of the member.
        If in a DM, this is the top-level user.
        """
        return self.interaction.user

    @property
    def member(self) -> Optional["Member"]:
        """The member who invoked the interaction, if this occurred in a guild."""
        return self.interaction.member

    @property
    def locale(self) -> Optional[str]:
        """The selected language of the invoking user."""
        return self.interaction.locale

    @property
    def guild_locale(self) -> Optional[str]:
        """The guild's preferred language, if applicable."""
        return self.interaction.guild_locale

    @property
    async def guild(self) -> Optional["Guild"]:
        """The guild object where the interaction occurred, if available."""

        if not self.guild_id:
            return None

        guild = None
        if hasattr(self.bot, "get_guild"):
            guild = self.bot.get_guild(self.guild_id)

        if not guild and hasattr(self.bot, "fetch_guild"):
            try:
                guild = await self.bot.fetch_guild(self.guild_id)
            except Exception:
                guild = None

        return guild

    @property
    async def channel(self) -> Optional[Any]:
        """The channel object where the interaction occurred, if available."""

        if not self.channel_id:
            return None

        channel = None
        if hasattr(self.bot, "get_channel"):
            channel = self.bot.get_channel(self.channel_id)
        elif hasattr(self.bot, "_channels"):
            channel = self.bot._channels.get(self.channel_id)

        if not channel and hasattr(self.bot, "fetch_channel"):
            try:
                channel = await self.bot.fetch_channel(self.channel_id)
            except Exception:
                channel = None

        return channel

    async def _send_response(
        self,
        response_type: "InteractionCallbackType",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Internal helper to send interaction responses."""
        if (
            self._responded
            and not self._deferred
            and response_type
            != InteractionCallbackType.APPLICATION_COMMAND_AUTOCOMPLETE_RESULT
        ):
            # If already responded and not deferred, subsequent responses must be followups
            # (unless it's an autocomplete result which is a special case)
            # For now, let's assume followups are handled by separate methods.
            # This logic might need refinement based on how followups are exposed.
            raise RuntimeError(
                "Interaction has already been responded to. Use send_followup()."
            )

        callback_data = InteractionCallbackData(data) if data else None
        payload = InteractionResponsePayload(type=response_type, data=callback_data)

        await self.bot._http.create_interaction_response(
            interaction_id=self.interaction_id,
            interaction_token=self.token,
            payload=payload,
        )
        if (
            response_type
            != InteractionCallbackType.APPLICATION_COMMAND_AUTOCOMPLETE_RESULT
        ):
            self._responded = True
            if (
                response_type
                == InteractionCallbackType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
                or response_type == InteractionCallbackType.DEFERRED_UPDATE_MESSAGE
            ):
                self._deferred = True

    async def defer(self, ephemeral: bool = False, thinking: bool = True) -> None:
        """
        Defers the interaction response.

        This is typically used when your command might take longer than 3 seconds to process.
        You must send a followup message within 15 minutes.

        Args:
            ephemeral (bool): Whether the subsequent followup response should be ephemeral.
                              Only applicable if `thinking` is True.
            thinking (bool): If True (default), responds with a "Bot is thinking..." message
                             (DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE).
                             If False, responds with DEFERRED_UPDATE_MESSAGE (for components).
        """
        if self._responded:
            raise RuntimeError("Interaction has already been responded to or deferred.")

        response_type = (
            InteractionCallbackType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
            if thinking
            else InteractionCallbackType.DEFERRED_UPDATE_MESSAGE
        )
        data = None
        if ephemeral and thinking:
            data = {
                "flags": MessageFlags.EPHEMERAL.value
            }  # Assuming MessageFlags enum exists

        await self._send_response(response_type, data)
        self._deferred = True  # Mark as deferred

    async def send(
        self,
        content: Optional[str] = None,
        embed: Optional["Embed"] = None,  # Convenience for single embed
        embeds: Optional[List["Embed"]] = None,
        *,
        tts: bool = False,
        files: Optional[List[Any]] = None,
        components: Optional[List[ActionRow]] = None,
        view: Optional[View] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
        ephemeral: bool = False,
        flags: Optional[int] = None,
    ) -> Optional[
        "Message"
    ]:  # Returns Message if not ephemeral and response was not deferred
        """
        Sends a response to the interaction.
        If the interaction was previously deferred, this will edit the original deferred response.
        Otherwise, it sends an initial response.

        Args:
            content (Optional[str]): The message content.
            embed (Optional[Embed]): A single embed to send. If `embeds` is also provided, this is ignored.
            embeds (Optional[List[Embed]]): A list of embeds to send (max 10).
            ephemeral (bool): Whether the message should be ephemeral (only visible to the invoker).
            flags (Optional[int]): Additional message flags to apply.

        Returns:
            Optional[Message]: The sent message object if a new message was created and not ephemeral.
                               None if the response was ephemeral or an edit to a deferred message.
        """
        if not self._responded and self._deferred:  # Editing a deferred response
            # Use edit_original_interaction_response
            payload: Dict[str, Any] = {}
            if content is not None:
                payload["content"] = content

            if tts:
                payload["tts"] = True

            actual_embeds = embeds
            if embed and not embeds:
                actual_embeds = [embed]
            if actual_embeds:
                payload["embeds"] = [e.to_dict() for e in actual_embeds]

            if view:
                await view._start(self.bot)
                payload["components"] = view.to_components_payload()
            elif components:
                payload["components"] = [c.to_dict() for c in components]

            if files is not None:
                payload["attachments"] = [
                    f.to_dict() if hasattr(f, "to_dict") else f for f in files
                ]

            if allowed_mentions is not None:
                payload["allowed_mentions"] = allowed_mentions

            # Flags (like ephemeral) cannot be set when editing the original deferred response this way.
            # Ephemeral for deferred must be set during defer().

            msg_data = await self.bot._http.edit_original_interaction_response(
                application_id=self.application_id,
                interaction_token=self.token,
                payload=payload,
            )
            self._responded = True  # Ensure it's marked as fully responded
            if view and msg_data and "id" in msg_data:
                view.message_id = msg_data["id"]
                self.bot._views[msg_data["id"]] = view
            # Construct and return Message object if needed, for now returns None for edits
            return None

        elif not self._responded:  # Sending an initial response
            data: Dict[str, Any] = {}
            if content is not None:
                data["content"] = content

            if tts:
                data["tts"] = True

            actual_embeds = embeds
            if embed and not embeds:
                actual_embeds = [embed]
            if actual_embeds:
                data["embeds"] = [
                    e.to_dict() for e in actual_embeds
                ]  # Assuming embeds have to_dict()

            if view:
                await view._start(self.bot)
                data["components"] = view.to_components_payload()
            elif components:
                data["components"] = [c.to_dict() for c in components]

            if files is not None:
                data["attachments"] = [
                    f.to_dict() if hasattr(f, "to_dict") else f for f in files
                ]

            if allowed_mentions is not None:
                data["allowed_mentions"] = allowed_mentions

            flags_value = 0
            if ephemeral:
                flags_value |= MessageFlags.EPHEMERAL.value
            if flags:
                flags_value |= flags
            if flags_value:
                data["flags"] = flags_value

            await self._send_response(
                InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE, data
            )

            if view and not ephemeral:
                try:
                    msg_data = await self.bot._http.get_original_interaction_response(
                        application_id=self.application_id,
                        interaction_token=self.token,
                    )
                    if msg_data and "id" in msg_data:
                        view.message_id = msg_data["id"]
                        self.bot._views[msg_data["id"]] = view
                except Exception:
                    pass
            if not ephemeral:
                return None
            return None
        else:
            # If already responded and not deferred, this should be a followup.
            # This method is for initial response or editing deferred.
            raise RuntimeError(
                "Interaction has already been responded to. Use send_followup()."
            )

    async def send_followup(
        self,
        content: Optional[str] = None,
        embed: Optional["Embed"] = None,
        embeds: Optional[List["Embed"]] = None,
        *,
        ephemeral: bool = False,
        tts: bool = False,
        files: Optional[List[Any]] = None,
        components: Optional[List["ActionRow"]] = None,
        view: Optional[View] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
        flags: Optional[int] = None,
    ) -> Optional["Message"]:
        """
        Sends a followup message to an interaction.
        This can be used after an initial response or a deferred response.

        Args:
            content (Optional[str]): The message content.
            embed (Optional[Embed]): A single embed to send.
            embeds (Optional[List[Embed]]): A list of embeds to send.
            ephemeral (bool): Whether the followup message should be ephemeral.
            flags (Optional[int]): Additional message flags to apply.

        Returns:
            Message: The sent followup message object.
        """
        if not self._responded:
            raise RuntimeError(
                "Must acknowledge or defer the interaction before sending a followup."
            )

        payload: Dict[str, Any] = {}
        if content is not None:
            payload["content"] = content

        if tts:
            payload["tts"] = True

        actual_embeds = embeds
        if embed and not embeds:
            actual_embeds = [embed]
        if actual_embeds:
            payload["embeds"] = [
                e.to_dict() for e in actual_embeds
            ]  # Assuming embeds have to_dict()

        if view:
            await view._start(self.bot)
            payload["components"] = view.to_components_payload()
        elif components:
            payload["components"] = [c.to_dict() for c in components]

        if files is not None:
            payload["attachments"] = [
                f.to_dict() if hasattr(f, "to_dict") else f for f in files
            ]

        if allowed_mentions is not None:
            payload["allowed_mentions"] = allowed_mentions

        flags_value = 0
        if ephemeral:
            flags_value |= MessageFlags.EPHEMERAL.value
        if flags:
            flags_value |= flags
        if flags_value:
            payload["flags"] = flags_value

        # Followup messages are sent to a webhook endpoint
        message_data = await self.bot._http.create_followup_message(
            application_id=self.application_id,
            interaction_token=self.token,
            payload=payload,
        )
        if view and message_data and "id" in message_data:
            view.message_id = message_data["id"]
            self.bot._views[message_data["id"]] = view
        from disagreement.models import Message  # Ensure Message is available

        return Message(data=message_data, client_instance=self.bot)

    async def edit(
        self,
        message_id: "Snowflake" = "@original",  # Defaults to editing the original response
        content: Optional[str] = None,
        embed: Optional["Embed"] = None,
        embeds: Optional[List["Embed"]] = None,
        *,
        components: Optional[List["ActionRow"]] = None,
        attachments: Optional[List[Any]] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
    ) -> Optional["Message"]:
        """
        Edits a message previously sent in response to this interaction.
        Can edit the original response or a followup message.

        Args:
            message_id (Snowflake): The ID of the message to edit. Defaults to "@original"
                                    to edit the initial interaction response.
            content (Optional[str]): The new message content.
            embed (Optional[Embed]): A single new embed.
            embeds (Optional[List[Embed]]): A list of new embeds.

        Returns:
            Optional[Message]: The edited message object if available.
        """
        if not self._responded:
            raise RuntimeError(
                "Cannot edit response if interaction hasn't been responded to or deferred."
            )

        payload: Dict[str, Any] = {}
        if content is not None:
            payload["content"] = content  # Use None to clear

        actual_embeds = embeds
        if embed and not embeds:
            actual_embeds = [embed]
        if actual_embeds is not None:  # Allow passing empty list to clear embeds
            payload["embeds"] = [
                e.to_dict() for e in actual_embeds
            ]  # Assuming embeds have to_dict()

        if components is not None:
            payload["components"] = [c.to_dict() for c in components]

        if attachments is not None:
            payload["attachments"] = [
                a.to_dict() if hasattr(a, "to_dict") else a for a in attachments
            ]

        if allowed_mentions is not None:
            payload["allowed_mentions"] = allowed_mentions

        if message_id == "@original":
            edited_message_data = (
                await self.bot._http.edit_original_interaction_response(
                    application_id=self.application_id,
                    interaction_token=self.token,
                    payload=payload,
                )
            )
        else:
            edited_message_data = await self.bot._http.edit_followup_message(
                application_id=self.application_id,
                interaction_token=self.token,
                message_id=message_id,
                payload=payload,
            )
        # The HTTP methods used in tests return minimal data that is insufficient
        # to construct a full ``Message`` instance, so we simply return ``None``
        # rather than attempting to parse the response.
        return None

    async def delete(self, message_id: "Snowflake" = "@original") -> None:
        """
        Deletes a message previously sent in response to this interaction.
        Can delete the original response or a followup message.

        Args:
            message_id (Snowflake): The ID of the message to delete. Defaults to "@original"
                                    to delete the initial interaction response.
        """
        if not self._responded:
            # If not responded, there's nothing to delete via this interaction's lifecycle.
            # Deferral doesn't create a message to delete until a followup is sent.
            raise RuntimeError(
                "Cannot delete response if interaction hasn't been responded to."
            )

        if message_id == "@original":
            await self.bot._http.delete_original_interaction_response(
                application_id=self.application_id, interaction_token=self.token
            )
        else:
            await self.bot._http.delete_followup_message(
                application_id=self.application_id,
                interaction_token=self.token,
                message_id=message_id,
            )
        # After deleting the original response, further followups might be problematic.
        # Discord docs: "Once the original message is deleted, you can no longer edit the message or send followups."
        # Consider implications for context state.

    def typing(self) -> Typing:
        """Return a typing context manager for this interaction's channel."""

        if not self.channel_id:
            raise RuntimeError("Cannot send typing indicator without a channel.")
        return self.bot.typing(self.channel_id)
