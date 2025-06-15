"""
HTTP client for interacting with the Discord REST API.
"""

import asyncio
import logging
import aiohttp  # pylint: disable=import-error
import json
from urllib.parse import quote
from typing import Optional, Dict, Any, Union, TYPE_CHECKING, List

from .errors import *  # Import all custom exceptions
from . import __version__  # For User-Agent
from .rate_limiter import RateLimiter
from .interactions import InteractionResponsePayload

if TYPE_CHECKING:
    from .client import Client
    from .models import Message, Webhook, File, StageInstance, Invite
    from .interactions import ApplicationCommand, Snowflake

# Discord API constants
API_BASE_URL = "https://discord.com/api/v10"  # Using API v10

logger = logging.getLogger(__name__)

DISCORD_ERROR_CODE_TO_EXCEPTION = {
    0: GeneralError,
    10001: UnknownAccount,
    10002: UnknownApplication,
    10003: UnknownChannel,
    10004: UnknownGuild,
    10005: UnknownIntegration,
    10006: UnknownInvite,
    10007: UnknownMember,
    10008: UnknownMessage,
    10009: UnknownPermissionOverwrite,
    10010: UnknownProvider,
    10011: UnknownRole,
    10012: UnknownToken,
    10013: UnknownUser,
    10014: UnknownEmoji,
    10015: UnknownWebhook,
    10016: UnknownWebhookService,
    10020: UnknownSession,
    10021: UnknownAsset,
    10026: UnknownBan,
    10027: UnknownSKU,
    10028: UnknownStoreListing,
    10029: UnknownEntitlement,
    10030: UnknownBuild,
    10031: UnknownLobby,
    10032: UnknownBranch,
    10033: UnknownStoreDirectoryLayout,
    10036: UnknownRedistributable,
    10038: UnknownGiftCode,
    10049: UnknownStream,
    10050: UnknownPremiumServerSubscribeCooldown,
    10057: UnknownGuildTemplate,
    10059: UnknownDiscoverableServerCategory,
    10060: UnknownSticker,
    10061: UnknownStickerPack,
    10062: UnknownInteraction,
    10063: UnknownApplicationCommand,
    10065: UnknownVoiceState,
    10066: UnknownApplicationCommandPermissions,
    10067: UnknownStageInstance,
    10068: UnknownGuildMemberVerificationForm,
    10069: UnknownGuildWelcomeScreen,
    10070: UnknownGuildScheduledEvent,
    10071: UnknownGuildScheduledEventUser,
    10087: UnknownTag,
    10097: UnknownSound,
    20001: BotsCannotUseThisEndpoint,
    20002: OnlyBotsCanUseThisEndpoint,
    20009: ExplicitContentCannotBeSentToTheDesiredRecipients,
    20012: NotAuthorizedToPerformThisActionOnThisApplication,
    20016: ActionCannotBePerformedDueToSlowmodeRateLimit,
    20018: OnlyTheOwnerOfThisAccountCanPerformThisAction,
    20022: MessageCannotBeEditedDueToAnnouncementRateLimits,
    20024: UnderMinimumAge,
    20028: ChannelHitWriteRateLimit,
    20029: ServerHitWriteRateLimit,
    20031: DisallowedWordsInStageTopicOrNames,
    20035: GuildPremiumSubscriptionLevelTooLow,
    30001: MaximumNumberOfGuildsReached,
    30002: MaximumNumberOfFriendsReached,
    30003: MaximumNumberOfPinsReached,
    30004: MaximumNumberOfRecipientsReached,
    30005: MaximumNumberOfGuildRolesReached,
    30007: MaximumNumberOfWebhooksReached,
    30008: MaximumNumberOfEmojisReached,
    30010: MaximumNumberOfReactionsReached,
    30011: MaximumNumberOfGroupDMsReached,
    30013: MaximumNumberOfGuildChannelsReached,
    30015: MaximumNumberOfAttachmentsInAMessageReached,
    30016: MaximumNumberOfInvitesReached,
    30018: MaximumNumberOfAnimatedEmojisReached,
    30019: MaximumNumberOfServerMembersReached,
    30030: MaximumNumberOfServerCategoriesReached,
    30031: GuildAlreadyHasATemplate,
    30032: MaximumNumberOfApplicationCommandsReached,
    30033: MaximumNumberOfThreadParticipantsReached,
    30034: MaximumNumberOfDailyApplicationCommandCreatesReached,
    30035: MaximumNumberOfBansForNonGuildMembersExceeded,
    30037: MaximumNumberOfBansFetchesReached,
    30038: MaximumNumberOfUncompletedGuildScheduledEventsReached,
    30039: MaximumNumberOfStickersReached,
    30040: MaximumNumberOfPruneRequestsReached,
    30042: MaximumNumberOfGuildWidgetSettingsUpdatesReached,
    30045: MaximumNumberOfSoundboardSoundsReached,
    30046: MaximumNumberOfEditsToMessagesOlderThan1HourReached,
    30047: MaximumNumberOfPinnedThreadsInAForumChannelReached,
    30048: MaximumNumberOfTagsInAForumChannelReached,
    30052: BitrateIsTooHighForChannelOfThisType,
    30056: MaximumNumberOfPremiumEmojisReached,
    30058: MaximumNumberOfWebhooksPerGuildReached,
    30061: MaximumNumberOfChannelPermissionOverwritesReached,
    30062: TheChannelsForThisGuildAreTooLarge,
    40001: Unauthorized,
    40002: YouNeedToVerifyYourAccount,
    40003: YouAreOpeningDirectMessagesTooFast,
    40004: SendMessagesHasBeenTemporarilyDisabled,
    40005: RequestEntityTooLarge,
    40006: ThisFeatureHasBeenTemporarilyDisabledServerSide,
    40007: TheUserIsBannedFromThisGuild,
    40012: ConnectionHasBeenRevoked,
    40018: OnlyConsumableSKUsCanBeConsumed,
    40019: YouCanOnlyDeleteSandboxEntitlements,
    40032: TargetUserIsNotConnectedToVoice,
    40033: ThisMessageHasAlreadyBeenCrossposted,
    40041: AnApplicationCommandWithThatNameAlreadyExists,
    40043: ApplicationInteractionFailedToSend,
    40058: CannotSendAMessageInAForumChannel,
    40060: InteractionHasAlreadyBeenAcknowledged,
    40061: TagNamesMustBeUnique,
    40062: ServiceResourceIsBeingRateLimited,
    40066: ThereAreNoTagsAvailableThatCanBeSetByNonModerators,
    40067: ATagIsRequiredToCreateAForumPostInThisChannel,
    40074: AnEntitlementHasAlreadyBeenGrantedForThisResource,
    40094: ThisInteractionHasHitTheMaximumNumberOfFollowUpMessages,
    40333: CloudflareIsBlockingYourRequest,
    50001: MissingAccess,
    50002: InvalidAccountType,
    50003: CannotExecuteActionOnADMChannel,
    50004: GuildWidgetDisabled,
    50005: CannotEditAMessageAuthoredByAnotherUser,
    50006: CannotSendAnEmptyMessage,
    50007: CannotSendMessagesToThisUser,
    50008: CannotSendMessagesInANonTextChannel,
    50009: ChannelVerificationLevelIsTooHighForYouToGainAccess,
    50010: OAuth2ApplicationDoesNotHaveABot,
    50011: OAuth2ApplicationLimitReached,
    50012: InvalidOAuth2State,
    50013: YouLackPermissionsToPerformThatAction,
    50014: InvalidAuthenticationTokenProvided,
    50015: NoteWasTooLong,
    50016: ProvidedTooFewOrTooManyMessagesToDelete,
    50017: InvalidMFALevel,
    50019: AMessageCanOnlyBePinnedToTheChannelItWasSentIn,
    50020: InviteCodeWasEitherInvalidOrTaken,
    50021: CannotExecuteActionOnASystemMessage,
    50024: CannotExecuteActionOnThisChannelType,
    50025: InvalidOAuth2AccessTokenProvided,
    50026: MissingRequiredOAuth2Scope,
    50027: InvalidWebhookTokenProvided,
    50028: InvalidRole,
    50033: InvalidRecipients,
    50034: AMessageProvidedWasTooOldToBulkDelete,
    50035: InvalidFormBody,
    50036: AnInviteWasAcceptedToAGuildTheApplicationBotIsNotIn,
    50039: InvalidActivityAction,
    50041: InvalidAPIVersionProvided,
    50045: FileUploadedExceedsTheMaximumSize,
    50046: InvalidFileUploaded,
    50054: CannotSelfRedeemThisGift,
    50055: InvalidGuild,
    50057: InvalidSKU,
    50067: InvalidRequestOrigin,
    50068: InvalidMessageType,
    50070: PaymentSourceRequiredToRedeemGift,
    50073: CannotModifyASystemWebhook,
    50074: CannotDeleteAChannelRequiredForCommunityGuilds,
    50080: CannotEditStickersWithinAMessage,
    50081: InvalidStickerSent,
    50083: TriedToPerformAnOperationOnAnArchivedThread,
    50085: InvalidThreadNotificationSettings,
    50086: BeforeValueIsEarlierThanTheThreadCreationDate,
    50087: CommunityServerChannelsMustBeTextChannels,
    50091: TheEntityTypeOfTheEventIsDifferentFromTheEntityYouAreTryingToStartTheEventFor,
    50095: ThisServerIsNotAvailableInYourLocation,
    50097: ThisServerNeedsMonetizationEnabledInOrderToPerformThisAction,
    50101: ThisServerNeedsMoreBoostsToPerformThisAction,
    50109: TheRequestBodyContainsInvalidJSON,
    50110: TheProvidedFileIsInvalid,
    50123: TheProvidedFileTypeIsInvalid,
    50124: TheProvidedFileDurationExceedsMaximumOf52Seconds,
    50131: OwnerCannotBePendingMember,
    50132: OwnershipCannotBeTransferredToABotUser,
    50138: FailedToResizeAssetBelowTheMaximumSize,
    50144: CannotMixSubscriptionAndNonSubscriptionRolesForAnEmoji,
    50145: CannotConvertBetweenPremiumEmojiAndNormalEmoji,
    50146: UploadedFileNotFound,
    50151: TheSpecifiedEmojiIsInvalid,
    50159: VoiceMessagesDoNotSupportAdditionalContent,
    50160: VoiceMessagesMustHaveASingleAudioAttachment,
    50161: VoiceMessagesMustHaveSupportingMetadata,
    50162: VoiceMessagesCannotBeEdited,
    50163: CannotDeleteGuildSubscriptionIntegration,
    50173: YouCannotSendVoiceMessagesInThisChannel,
    50178: TheUserAccountMustFirstBeVerified,
    50192: TheProvidedFileDoesNotHaveAValidDuration,
    50600: YouDoNotHavePermissionToSendThisSticker,
    60003: TwoFactorIsRequiredForThisOperation,
    80004: NoUsersWithDiscordTagExist,
    90001: ReactionWasBlocked,
    90002: UserCannotUseBurstReactions,
    110001: ApplicationNotYetAvailable,
    130000: APIResourceIsCurrentlyOverloaded,
    150006: TheStageIsAlreadyOpen,
    160002: CannotReplyWithoutPermissionToReadMessageHistory,
    160004: AThreadHasAlreadyBeenCreatedForThisMessage,
    160005: ThreadIsLocked,
    160006: MaximumNumberOfActiveThreadsReached,
    160007: MaximumNumberOfActiveAnnouncementThreadsReached,
    170001: InvalidJSONForUploadedLottieFile,
    170002: UploadedLottiesCannotContainRasterizedImages,
    170003: StickerMaximumFramerateExceeded,
    170004: StickerFrameCountExceedsMaximumOf1000Frames,
    170005: LottieAnimationMaximumDimensionsExceeded,
    170006: StickerFrameRateIsEitherTooSmallOrTooLarge,
    170007: StickerAnimationDurationExceedsMaximumOf5Seconds,
    180000: CannotUpdateAFinishedEvent,
    180002: FailedToCreateStageNeededForStageEvent,
    200000: MessageWasBlockedByAutomaticModeration,
    200001: TitleWasBlockedByAutomaticModeration,
    220001: WebhooksPostedToForumChannelsMustHaveAThreadNameOrThreadId,
    220002: WebhooksPostedToForumChannelsCannotHaveBothAThreadNameAndThreadId,
    220003: WebhooksCanOnlyCreateThreadsInForumChannels,
    220004: WebhookServicesCannotBeUsedInForumChannels,
    240000: MessageBlockedByHarmfulLinksFilter,
    350000: CannotEnableOnboardingRequirementsAreNotMet,
    350001: CannotUpdateOnboardingWhileBelowRequirements,
    500000: FailedToBanUsers,
    520000: PollVotingBlocked,
    520001: PollExpired,
    520002: InvalidChannelTypeForPollCreation,
    520003: CannotEditAPollMessage,
    520004: CannotUseAnEmojiIncludedWithThePoll,
    520006: CannotExpireANonPollMessage,
}


class HTTPClient:
    """Handles HTTP requests to the Discord API."""

    def __init__(
        self,
        token: str,
        client_session: Optional[aiohttp.ClientSession] = None,
        verbose: bool = False,
        **session_kwargs: Any,
    ):
        """Create a new HTTP client.

        Parameters
        ----------
        token:
            Bot token for authentication.
        client_session:
            Optional existing :class:`aiohttp.ClientSession`.
        verbose:
            If ``True``, log HTTP requests and responses.
        **session_kwargs:
            Additional options forwarded to :class:`aiohttp.ClientSession`, such
            as ``proxy`` or ``connector``.
        """

        self.token = token
        self._session: Optional[aiohttp.ClientSession] = client_session
        self._session_kwargs: Dict[str, Any] = session_kwargs
        self.user_agent = f"DiscordBot (https://github.com/Slipstreamm/disagreement, {__version__})"  # Customize URL

        self.verbose = verbose

        self._rate_limiter = RateLimiter()

    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(**self._session_kwargs)

    async def close(self):
        """Closes the underlying aiohttp.ClientSession."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[
            Union[Dict[str, Any], List[Dict[str, Any]], aiohttp.FormData]
        ] = None,
        params: Optional[Dict[str, Any]] = None,
        is_json: bool = True,
        use_auth_header: bool = True,
        custom_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Makes an HTTP request to the Discord API."""
        await self._ensure_session()

        url = f"{API_BASE_URL}{endpoint}"
        final_headers: Dict[str, str] = {  # Renamed to final_headers
            "User-Agent": self.user_agent,
        }
        if use_auth_header:
            final_headers["Authorization"] = f"Bot {self.token}"

        if is_json and payload:
            final_headers["Content-Type"] = "application/json"

        if custom_headers:  # Merge custom headers
            final_headers.update(custom_headers)

        if self.verbose:
            logger.debug(
                "HTTP REQUEST: %s %s | payload=%s params=%s",
                method,
                url,
                payload,
                params,
            )

        route = f"{method.upper()}:{endpoint}"

        for attempt in range(5):  # Max 5 retries for rate limits
            await self._rate_limiter.acquire(route)
            assert self._session is not None, "ClientSession not initialized"
            async with self._session.request(
                method,
                url,
                json=payload if is_json else None,
                data=payload if not is_json else None,
                headers=final_headers,
                params=params,
            ) as response:

                data = None
                try:
                    if response.headers.get("Content-Type", "").startswith(
                        "application/json"
                    ):
                        data = await response.json()
                    else:
                        # For non-JSON responses, like fetching images or other files
                        # We might return the raw response or handle it differently
                        # For now, let's assume most API calls expect JSON
                        data = await response.text()
                except (aiohttp.ContentTypeError, json.JSONDecodeError):
                    data = (
                        await response.text()
                    )  # Fallback to text if JSON parsing fails

                if self.verbose:
                    logger.debug(
                        "HTTP RESPONSE: %s %s | %s", response.status, url, data
                    )

                self._rate_limiter.release(route, response.headers)

                if 200 <= response.status < 300:
                    if response.status == 204:
                        return None
                    return data

                # Rate limit handling
                if response.status == 429:  # Rate limited
                    retry_after_str = response.headers.get("Retry-After", "1")
                    try:
                        retry_after = float(retry_after_str)
                    except ValueError:
                        retry_after = 1.0  # Default retry if header is malformed

                    is_global = (
                        response.headers.get("X-RateLimit-Global", "false").lower()
                        == "true"
                    )

                    error_message = f"Rate limited on {method} {endpoint}."
                    if data and isinstance(data, dict) and "message" in data:
                        error_message += f" Discord says: {data['message']}"

                    await self._rate_limiter.handle_rate_limit(
                        route, retry_after, is_global
                    )

                    if attempt < 4:  # Don't log on the last attempt before raising
                        logger.warning(
                            "%s Retrying after %ss (Attempt %s/5). Global: %s",
                            error_message,
                            retry_after,
                            attempt + 1,
                            is_global,
                        )
                        continue  # Retry the request
                    else:  # Last attempt failed
                        raise RateLimitError(
                            response,
                            message=error_message,
                            retry_after=retry_after,
                            is_global=is_global,
                        )

                # Other error handling
                if response.status == 401:  # Unauthorized
                    raise AuthenticationError(response, "Invalid token provided.")
                if response.status == 403:  # Forbidden
                    raise HTTPException(
                        response,
                        "Missing permissions or access denied.",
                        status=response.status,
                        text=str(data),
                    )

                # General HTTP error
                error_text = str(data) if data else "Unknown error"
                discord_error_code = (
                    data.get("code") if isinstance(data, dict) else None
                )

                if discord_error_code in DISCORD_ERROR_CODE_TO_EXCEPTION:
                    exc_class = DISCORD_ERROR_CODE_TO_EXCEPTION[discord_error_code]
                    raise exc_class(
                        response,
                        f"API Error on {method} {endpoint}: {error_text}",
                        status=response.status,
                        text=error_text,
                        error_code=discord_error_code,
                    )

                raise HTTPException(
                    response,
                    f"API Error on {method} {endpoint}: {error_text}",
                    status=response.status,
                    text=error_text,
                    error_code=discord_error_code,
                )
        raise DisagreementException(
            f"Failed request to {method} {endpoint} after multiple retries."
        )

    # --- Specific API call methods ---

    async def get_gateway_bot(self) -> Dict[str, Any]:
        """Gets the WSS URL and sharding information for the Gateway."""
        return await self.request("GET", "/gateway/bot")

    async def send_message(
        self,
        channel_id: str,
        content: Optional[str] = None,
        tts: bool = False,
        embeds: Optional[List[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        allowed_mentions: Optional[dict] = None,
        message_reference: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Any]] = None,
        files: Optional[List[Any]] = None,
        flags: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Sends a message to a channel.

        Parameters
        ----------
        attachments:
            A list of attachment payloads to include with the message.
        files:
            A list of :class:`File` objects containing binary data to upload.

        Returns
        -------
        Dict[str, Any]
            The created message data.
        """
        payload: Dict[str, Any] = {}
        if content is not None:  # Content is optional if embeds/components are present
            payload["content"] = content
        if tts:
            payload["tts"] = True
        if embeds:
            payload["embeds"] = embeds
        if components:
            payload["components"] = components
        if allowed_mentions:
            payload["allowed_mentions"] = allowed_mentions
        all_files: List["File"] = []
        if attachments is not None:
            payload["attachments"] = []
            for a in attachments:
                if hasattr(a, "data") and hasattr(a, "filename"):
                    idx = len(all_files)
                    all_files.append(a)
                    payload["attachments"].append({"id": idx, "filename": a.filename})
                else:
                    payload["attachments"].append(
                        a.to_dict() if hasattr(a, "to_dict") else a
                    )
        if files is not None:
            for f in files:
                if hasattr(f, "data") and hasattr(f, "filename"):
                    idx = len(all_files)
                    all_files.append(f)
                    if "attachments" not in payload:
                        payload["attachments"] = []
                    payload["attachments"].append({"id": idx, "filename": f.filename})
                else:
                    raise TypeError("files must be File objects")
        if flags:
            payload["flags"] = flags
        if message_reference:
            payload["message_reference"] = message_reference

        if not payload:
            raise ValueError("Message must have content, embeds, or components.")

        if all_files:
            form = aiohttp.FormData()
            form.add_field(
                "payload_json", json.dumps(payload), content_type="application/json"
            )
            for idx, f in enumerate(all_files):
                form.add_field(
                    f"files[{idx}]",
                    f.data,
                    filename=f.filename,
                    content_type="application/octet-stream",
                )
            return await self.request(
                "POST",
                f"/channels/{channel_id}/messages",
                payload=form,
                is_json=False,
            )

        return await self.request(
            "POST", f"/channels/{channel_id}/messages", payload=payload
        )

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Edits a message in a channel."""

        return await self.request(
            "PATCH",
            f"/channels/{channel_id}/messages/{message_id}",
            payload=payload,
        )

    async def get_message(
        self, channel_id: "Snowflake", message_id: "Snowflake"
    ) -> Dict[str, Any]:
        """Fetches a message from a channel."""

        return await self.request(
            "GET", f"/channels/{channel_id}/messages/{message_id}"
        )

    async def delete_message(
        self, channel_id: "Snowflake", message_id: "Snowflake"
    ) -> None:
        """Deletes a message in a channel."""

        await self.request("DELETE", f"/channels/{channel_id}/messages/{message_id}")

    async def create_reaction(
        self, channel_id: "Snowflake", message_id: "Snowflake", emoji: str
    ) -> None:
        """Adds a reaction to a message as the current user."""
        encoded = quote(emoji)
        await self.request(
            "PUT",
            f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded}/@me",
        )

    async def delete_reaction(
        self, channel_id: "Snowflake", message_id: "Snowflake", emoji: str
    ) -> None:
        """Removes the current user's reaction from a message."""
        encoded = quote(emoji)
        await self.request(
            "DELETE",
            f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded}/@me",
        )

    async def delete_user_reaction(
        self,
        channel_id: "Snowflake",
        message_id: "Snowflake",
        emoji: str,
        user_id: "Snowflake",
    ) -> None:
        """Removes another user's reaction from a message."""
        encoded = quote(emoji)
        await self.request(
            "DELETE",
            f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded}/{user_id}",
        )

    async def get_reactions(
        self, channel_id: "Snowflake", message_id: "Snowflake", emoji: str
    ) -> List[Dict[str, Any]]:
        """Fetches the users that reacted with a specific emoji."""
        encoded = quote(emoji)
        return await self.request(
            "GET",
            f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded}",
        )

    async def clear_reactions(
        self, channel_id: "Snowflake", message_id: "Snowflake"
    ) -> None:
        """Removes all reactions from a message."""

        await self.request(
            "DELETE",
            f"/channels/{channel_id}/messages/{message_id}/reactions",
        )

    async def bulk_delete_messages(
        self, channel_id: "Snowflake", messages: List["Snowflake"]
    ) -> List["Snowflake"]:
        """Bulk deletes messages in a channel and returns their IDs."""

        await self.request(
            "POST",
            f"/channels/{channel_id}/messages/bulk-delete",
            payload={"messages": messages},
        )
        return messages

    async def get_pinned_messages(
        self, channel_id: "Snowflake"
    ) -> List[Dict[str, Any]]:
        """Fetches all pinned messages in a channel."""

        return await self.request("GET", f"/channels/{channel_id}/pins")

    async def pin_message(
        self, channel_id: "Snowflake", message_id: "Snowflake"
    ) -> None:
        """Pins a message in a channel."""

        await self.request("PUT", f"/channels/{channel_id}/pins/{message_id}")

    async def unpin_message(
        self, channel_id: "Snowflake", message_id: "Snowflake"
    ) -> None:
        """Unpins a message from a channel."""

        await self.request("DELETE", f"/channels/{channel_id}/pins/{message_id}")

    async def delete_channel(
        self, channel_id: str, reason: Optional[str] = None
    ) -> None:
        """Deletes a channel.

        If the channel is a guild channel, requires the MANAGE_CHANNELS permission.
        If the channel is a thread, requires the MANAGE_THREADS permission (if locked) or
        be the thread creator (if not locked).
        Deleting a category does not delete its child channels.
        """
        custom_headers = {}
        if reason:
            custom_headers["X-Audit-Log-Reason"] = reason

        await self.request(
            "DELETE",
            f"/channels/{channel_id}",
            custom_headers=custom_headers if custom_headers else None,
        )

    async def edit_channel(
        self,
        channel_id: "Snowflake",
        payload: Dict[str, Any],
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Edits a channel."""
        headers = {"X-Audit-Log-Reason": reason} if reason else None
        return await self.request(
            "PATCH",
            f"/channels/{channel_id}",
            payload=payload,
            custom_headers=headers,
        )

    async def get_channel(self, channel_id: str) -> Dict[str, Any]:
        """Fetches a channel by ID."""
        return await self.request("GET", f"/channels/{channel_id}")

    async def get_channel_invites(
        self, channel_id: "Snowflake"
    ) -> List[Dict[str, Any]]:
        """Fetches the invites for a channel."""

        return await self.request("GET", f"/channels/{channel_id}/invites")

    async def create_invite(
        self, channel_id: "Snowflake", payload: Dict[str, Any]
    ) -> "Invite":
        """Creates an invite for a channel."""

        data = await self.request(
            "POST", f"/channels/{channel_id}/invites", payload=payload
        )
        from .models import Invite

        return Invite.from_dict(data)

    async def delete_invite(self, code: str) -> None:
        """Deletes an invite by code."""

        await self.request("DELETE", f"/invites/{code}")

    async def create_webhook(
        self, channel_id: "Snowflake", payload: Dict[str, Any]
    ) -> "Webhook":
        """Creates a webhook in the specified channel."""

        data = await self.request(
            "POST", f"/channels/{channel_id}/webhooks", payload=payload
        )
        from .models import Webhook

        return Webhook(data)

    async def edit_webhook(
        self, webhook_id: "Snowflake", payload: Dict[str, Any]
    ) -> "Webhook":
        """Edits an existing webhook."""

        data = await self.request("PATCH", f"/webhooks/{webhook_id}", payload=payload)
        from .models import Webhook

        return Webhook(data)

    async def delete_webhook(self, webhook_id: "Snowflake") -> None:
        """Deletes a webhook."""

        await self.request("DELETE", f"/webhooks/{webhook_id}")

    async def execute_webhook(
        self,
        webhook_id: "Snowflake",
        token: str,
        *,
        content: Optional[str] = None,
        tts: bool = False,
        embeds: Optional[List[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        allowed_mentions: Optional[dict] = None,
        attachments: Optional[List[Any]] = None,
        files: Optional[List[Any]] = None,
        flags: Optional[int] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes a webhook and returns the created message."""

        payload: Dict[str, Any] = {}
        if content is not None:
            payload["content"] = content
        if tts:
            payload["tts"] = True
        if embeds:
            payload["embeds"] = embeds
        if components:
            payload["components"] = components
        if allowed_mentions:
            payload["allowed_mentions"] = allowed_mentions
        if username:
            payload["username"] = username
        if avatar_url:
            payload["avatar_url"] = avatar_url

        all_files: List["File"] = []
        if attachments is not None:
            payload["attachments"] = []
            for a in attachments:
                if hasattr(a, "data") and hasattr(a, "filename"):
                    idx = len(all_files)
                    all_files.append(a)
                    payload["attachments"].append({"id": idx, "filename": a.filename})
                else:
                    payload["attachments"].append(
                        a.to_dict() if hasattr(a, "to_dict") else a
                    )
        if files is not None:
            for f in files:
                if hasattr(f, "data") and hasattr(f, "filename"):
                    idx = len(all_files)
                    all_files.append(f)
                    if "attachments" not in payload:
                        payload["attachments"] = []
                    payload["attachments"].append({"id": idx, "filename": f.filename})
                else:
                    raise TypeError("files must be File objects")
        if flags:
            payload["flags"] = flags

        if all_files:
            form = aiohttp.FormData()
            form.add_field(
                "payload_json", json.dumps(payload), content_type="application/json"
            )
            for idx, f in enumerate(all_files):
                form.add_field(
                    f"files[{idx}]",
                    f.data,
                    filename=f.filename,
                    content_type="application/octet-stream",
                )
            return await self.request(
                "POST",
                f"/webhooks/{webhook_id}/{token}",
                payload=form,
                is_json=False,
                use_auth_header=False,
            )

        return await self.request(
            "POST",
            f"/webhooks/{webhook_id}/{token}",
            payload=payload,
            use_auth_header=False,
        )

    async def get_user(self, user_id: "Snowflake") -> Dict[str, Any]:
        """Fetches a user object for a given user ID."""
        return await self.request("GET", f"/users/{user_id}")

    async def get_current_user_guilds(self) -> List[Dict[str, Any]]:
        """Returns the guilds the current user is in."""
        return await self.request("GET", "/users/@me/guilds")

    async def get_guild_member(
        self, guild_id: "Snowflake", user_id: "Snowflake"
    ) -> Dict[str, Any]:
        """Returns a guild member object for the specified user."""
        return await self.request("GET", f"/guilds/{guild_id}/members/{user_id}")

    async def kick_member(
        self, guild_id: "Snowflake", user_id: "Snowflake", reason: Optional[str] = None
    ) -> None:
        """Kicks a member from the guild."""
        headers = {"X-Audit-Log-Reason": reason} if reason else None
        await self.request(
            "DELETE",
            f"/guilds/{guild_id}/members/{user_id}",
            custom_headers=headers,
        )

    async def ban_member(
        self,
        guild_id: "Snowflake",
        user_id: "Snowflake",
        *,
        delete_message_seconds: int = 0,
        reason: Optional[str] = None,
    ) -> None:
        """Bans a member from the guild."""
        payload = {}
        if delete_message_seconds:
            payload["delete_message_seconds"] = delete_message_seconds
        headers = {"X-Audit-Log-Reason": reason} if reason else None
        await self.request(
            "PUT",
            f"/guilds/{guild_id}/bans/{user_id}",
            payload=payload if payload else None,
            custom_headers=headers,
        )

    async def timeout_member(
        self,
        guild_id: "Snowflake",
        user_id: "Snowflake",
        *,
        until: Optional[str],
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Times out a member until the given ISO8601 timestamp."""
        payload = {"communication_disabled_until": until}
        headers = {"X-Audit-Log-Reason": reason} if reason else None
        return await self.request(
            "PATCH",
            f"/guilds/{guild_id}/members/{user_id}",
            payload=payload,
            custom_headers=headers,
        )

    async def get_guild_roles(self, guild_id: "Snowflake") -> List[Dict[str, Any]]:
        """Returns a list of role objects for the guild."""
        return await self.request("GET", f"/guilds/{guild_id}/roles")

    async def get_guild(self, guild_id: "Snowflake") -> Dict[str, Any]:
        """Fetches a guild object for a given guild ID."""
        return await self.request("GET", f"/guilds/{guild_id}")

    async def get_guild_widget(self, guild_id: "Snowflake") -> Dict[str, Any]:
        """Fetches the guild widget settings."""

        return await self.request("GET", f"/guilds/{guild_id}/widget")

    async def edit_guild_widget(
        self, guild_id: "Snowflake", payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Edits the guild widget settings."""

        return await self.request(
            "PATCH", f"/guilds/{guild_id}/widget", payload=payload
        )

    async def get_guild_templates(self, guild_id: "Snowflake") -> List[Dict[str, Any]]:
        """Fetches all templates for the given guild."""
        return await self.request("GET", f"/guilds/{guild_id}/templates")

    async def create_guild_template(
        self, guild_id: "Snowflake", payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates a guild template."""
        return await self.request(
            "POST", f"/guilds/{guild_id}/templates", payload=payload
        )

    async def sync_guild_template(
        self, guild_id: "Snowflake", template_code: str
    ) -> Dict[str, Any]:
        """Syncs a guild template to the guild's current state."""
        return await self.request(
            "PUT",
            f"/guilds/{guild_id}/templates/{template_code}",
        )

    async def delete_guild_template(
        self, guild_id: "Snowflake", template_code: str
    ) -> None:
        """Deletes a guild template."""
        await self.request("DELETE", f"/guilds/{guild_id}/templates/{template_code}")

    async def get_guild_scheduled_events(
        self, guild_id: "Snowflake"
    ) -> List[Dict[str, Any]]:
        """Returns a list of scheduled events for the guild."""

        return await self.request("GET", f"/guilds/{guild_id}/scheduled-events")

    async def get_guild_scheduled_event(
        self, guild_id: "Snowflake", event_id: "Snowflake"
    ) -> Dict[str, Any]:
        """Returns a guild scheduled event."""

        return await self.request(
            "GET", f"/guilds/{guild_id}/scheduled-events/{event_id}"
        )

    async def create_guild_scheduled_event(
        self, guild_id: "Snowflake", payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates a guild scheduled event."""

        return await self.request(
            "POST", f"/guilds/{guild_id}/scheduled-events", payload=payload
        )

    async def edit_guild_scheduled_event(
        self, guild_id: "Snowflake", event_id: "Snowflake", payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Edits a guild scheduled event."""

        return await self.request(
            "PATCH",
            f"/guilds/{guild_id}/scheduled-events/{event_id}",
            payload=payload,
        )

    async def delete_guild_scheduled_event(
        self, guild_id: "Snowflake", event_id: "Snowflake"
    ) -> None:
        """Deletes a guild scheduled event."""

        await self.request("DELETE", f"/guilds/{guild_id}/scheduled-events/{event_id}")

    async def get_audit_logs(
        self, guild_id: "Snowflake", **filters: Any
    ) -> Dict[str, Any]:
        """Fetches audit log entries for a guild."""
        params = {k: v for k, v in filters.items() if v is not None}
        return await self.request(
            "GET",
            f"/guilds/{guild_id}/audit-logs",
            params=params if params else None,
        )

    # Add other methods like:
    # async def get_guild(self, guild_id: str) -> Dict[str, Any]: ...
    # async def create_reaction(self, channel_id: str, message_id: str, emoji: str) -> None: ...
    # etc.
    # --- Application Command Endpoints ---

    # Global Application Commands
    async def get_global_application_commands(
        self, application_id: "Snowflake", with_localizations: bool = False
    ) -> List["ApplicationCommand"]:
        """Fetches all global commands for your application."""
        params = {"with_localizations": str(with_localizations).lower()}
        data = await self.request(
            "GET", f"/applications/{application_id}/commands", params=params
        )
        from .interactions import ApplicationCommand  # Ensure constructor is available

        return [ApplicationCommand(cmd_data) for cmd_data in data]

    async def create_global_application_command(
        self, application_id: "Snowflake", payload: Dict[str, Any]
    ) -> "ApplicationCommand":
        """Creates a new global command."""
        data = await self.request(
            "POST", f"/applications/{application_id}/commands", payload=payload
        )
        from .interactions import ApplicationCommand

        return ApplicationCommand(data)

    async def get_global_application_command(
        self, application_id: "Snowflake", command_id: "Snowflake"
    ) -> "ApplicationCommand":
        """Fetches a specific global command."""
        data = await self.request(
            "GET", f"/applications/{application_id}/commands/{command_id}"
        )
        from .interactions import ApplicationCommand

        return ApplicationCommand(data)

    async def edit_global_application_command(
        self,
        application_id: "Snowflake",
        command_id: "Snowflake",
        payload: Dict[str, Any],
    ) -> "ApplicationCommand":
        """Edits a specific global command."""
        data = await self.request(
            "PATCH",
            f"/applications/{application_id}/commands/{command_id}",
            payload=payload,
        )
        from .interactions import ApplicationCommand

        return ApplicationCommand(data)

    async def delete_global_application_command(
        self, application_id: "Snowflake", command_id: "Snowflake"
    ) -> None:
        """Deletes a specific global command."""
        await self.request(
            "DELETE", f"/applications/{application_id}/commands/{command_id}"
        )

    async def bulk_overwrite_global_application_commands(
        self, application_id: "Snowflake", payload: List[Dict[str, Any]]
    ) -> List["ApplicationCommand"]:
        """Bulk overwrites all global commands for your application."""
        data = await self.request(
            "PUT", f"/applications/{application_id}/commands", payload=payload
        )
        from .interactions import ApplicationCommand

        return [ApplicationCommand(cmd_data) for cmd_data in data]

    # Guild Application Commands
    async def get_guild_application_commands(
        self,
        application_id: "Snowflake",
        guild_id: "Snowflake",
        with_localizations: bool = False,
    ) -> List["ApplicationCommand"]:
        """Fetches all commands for your application for a specific guild."""
        params = {"with_localizations": str(with_localizations).lower()}
        data = await self.request(
            "GET",
            f"/applications/{application_id}/guilds/{guild_id}/commands",
            params=params,
        )
        from .interactions import ApplicationCommand

        return [ApplicationCommand(cmd_data) for cmd_data in data]

    async def create_guild_application_command(
        self,
        application_id: "Snowflake",
        guild_id: "Snowflake",
        payload: Dict[str, Any],
    ) -> "ApplicationCommand":
        """Creates a new guild command."""
        data = await self.request(
            "POST",
            f"/applications/{application_id}/guilds/{guild_id}/commands",
            payload=payload,
        )
        from .interactions import ApplicationCommand

        return ApplicationCommand(data)

    async def get_guild_application_command(
        self,
        application_id: "Snowflake",
        guild_id: "Snowflake",
        command_id: "Snowflake",
    ) -> "ApplicationCommand":
        """Fetches a specific guild command."""
        data = await self.request(
            "GET",
            f"/applications/{application_id}/guilds/{guild_id}/commands/{command_id}",
        )
        from .interactions import ApplicationCommand

        return ApplicationCommand(data)

    async def edit_guild_application_command(
        self,
        application_id: "Snowflake",
        guild_id: "Snowflake",
        command_id: "Snowflake",
        payload: Dict[str, Any],
    ) -> "ApplicationCommand":
        """Edits a specific guild command."""
        data = await self.request(
            "PATCH",
            f"/applications/{application_id}/guilds/{guild_id}/commands/{command_id}",
            payload=payload,
        )
        from .interactions import ApplicationCommand

        return ApplicationCommand(data)

    async def delete_guild_application_command(
        self,
        application_id: "Snowflake",
        guild_id: "Snowflake",
        command_id: "Snowflake",
    ) -> None:
        """Deletes a specific guild command."""
        await self.request(
            "DELETE",
            f"/applications/{application_id}/guilds/{guild_id}/commands/{command_id}",
        )

    async def bulk_overwrite_guild_application_commands(
        self,
        application_id: "Snowflake",
        guild_id: "Snowflake",
        payload: List[Dict[str, Any]],
    ) -> List["ApplicationCommand"]:
        """Bulk overwrites all commands for your application for a specific guild."""
        data = await self.request(
            "PUT",
            f"/applications/{application_id}/guilds/{guild_id}/commands",
            payload=payload,
        )
        from .interactions import ApplicationCommand

        return [ApplicationCommand(cmd_data) for cmd_data in data]

    # --- Interaction Response Endpoints ---
    # Note: These methods return Dict[str, Any] representing the Message data.
    # The caller (e.g., AppCommandHandler) will be responsible for constructing Message models
    # if needed, as Message model instantiation requires a `client_instance`.

    async def create_interaction_response(
        self,
        interaction_id: "Snowflake",
        interaction_token: str,
        payload: Union["InteractionResponsePayload", Dict[str, Any]],
        *,
        ephemeral: bool = False,
    ) -> None:
        """Creates a response to an Interaction.

        Parameters
        ----------
        ephemeral: bool
            Ignored parameter for test compatibility.
        """
        # Interaction responses do not use the bot token in the Authorization header.
        # They are authenticated by the interaction_token in the URL.
        payload_data: Dict[str, Any]
        if isinstance(payload, InteractionResponsePayload):
            payload_data = payload.to_dict()
        else:
            payload_data = payload

        await self.request(
            "POST",
            f"/interactions/{interaction_id}/{interaction_token}/callback",
            payload=payload_data,
            use_auth_header=False,
        )

    async def get_original_interaction_response(
        self, application_id: "Snowflake", interaction_token: str
    ) -> Dict[str, Any]:
        """Gets the initial Interaction response."""
        # This endpoint uses the bot token for auth.
        return await self.request(
            "GET", f"/webhooks/{application_id}/{interaction_token}/messages/@original"
        )

    async def edit_original_interaction_response(
        self,
        application_id: "Snowflake",
        interaction_token: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Edits the initial Interaction response."""
        return await self.request(
            "PATCH",
            f"/webhooks/{application_id}/{interaction_token}/messages/@original",
            payload=payload,
            use_auth_header=False,
        )  # Docs imply webhook-style auth

    async def delete_original_interaction_response(
        self, application_id: "Snowflake", interaction_token: str
    ) -> None:
        """Deletes the initial Interaction response."""
        await self.request(
            "DELETE",
            f"/webhooks/{application_id}/{interaction_token}/messages/@original",
            use_auth_header=False,
        )  # Docs imply webhook-style auth

    async def create_followup_message(
        self,
        application_id: "Snowflake",
        interaction_token: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Creates a followup message for an Interaction."""
        # Followup messages are sent to a webhook endpoint.
        return await self.request(
            "POST",
            f"/webhooks/{application_id}/{interaction_token}",
            payload=payload,
            use_auth_header=False,
        )  # Docs imply webhook-style auth

    async def edit_followup_message(
        self,
        application_id: "Snowflake",
        interaction_token: str,
        message_id: "Snowflake",
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Edits a followup message for an Interaction."""
        return await self.request(
            "PATCH",
            f"/webhooks/{application_id}/{interaction_token}/messages/{message_id}",
            payload=payload,
            use_auth_header=False,
        )  # Docs imply webhook-style auth

    async def delete_followup_message(
        self,
        application_id: "Snowflake",
        interaction_token: str,
        message_id: "Snowflake",
    ) -> None:
        """Deletes a followup message for an Interaction."""
        await self.request(
            "DELETE",
            f"/webhooks/{application_id}/{interaction_token}/messages/{message_id}",
            use_auth_header=False,
        )

    async def trigger_typing(self, channel_id: str) -> None:
        """Sends a typing indicator to the specified channel."""
        await self.request("POST", f"/channels/{channel_id}/typing")

    async def start_stage_instance(
        self, payload: Dict[str, Any], reason: Optional[str] = None
    ) -> "StageInstance":
        """Starts a stage instance."""

        headers = {"X-Audit-Log-Reason": reason} if reason else None
        data = await self.request(
            "POST", "/stage-instances", payload=payload, custom_headers=headers
        )
        from .models import StageInstance

        return StageInstance(data)

    async def edit_stage_instance(
        self,
        channel_id: "Snowflake",
        payload: Dict[str, Any],
        reason: Optional[str] = None,
    ) -> "StageInstance":
        """Edits an existing stage instance."""

        headers = {"X-Audit-Log-Reason": reason} if reason else None
        data = await self.request(
            "PATCH",
            f"/stage-instances/{channel_id}",
            payload=payload,
            custom_headers=headers,
        )
        from .models import StageInstance

        return StageInstance(data)

    async def end_stage_instance(
        self, channel_id: "Snowflake", reason: Optional[str] = None
    ) -> None:
        """Ends a stage instance."""

        headers = {"X-Audit-Log-Reason": reason} if reason else None
        await self.request(
            "DELETE", f"/stage-instances/{channel_id}", custom_headers=headers
        )

    async def get_voice_regions(self) -> List[Dict[str, Any]]:
        """Returns available voice regions."""
        return await self.request("GET", "/voice/regions")

    async def start_thread_from_message(
        self,
        channel_id: "Snowflake",
        message_id: "Snowflake",
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Starts a new thread from an existing message."""
        return await self.request(
            "POST",
            f"/channels/{channel_id}/messages/{message_id}/threads",
            payload=payload,
        )

    async def start_thread_without_message(
        self, channel_id: "Snowflake", payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Starts a new thread that is not attached to a message."""
        return await self.request(
            "POST", f"/channels/{channel_id}/threads", payload=payload
        )

    async def join_thread(self, channel_id: "Snowflake") -> None:
        """Joins the current user to a thread."""
        await self.request("PUT", f"/channels/{channel_id}/thread-members/@me")

    async def leave_thread(self, channel_id: "Snowflake") -> None:
        """Removes the current user from a thread."""
        await self.request("DELETE", f"/channels/{channel_id}/thread-members/@me")

    async def create_dm(self, recipient_id: "Snowflake") -> Dict[str, Any]:
        """Creates (or opens) a DM channel with the given user."""
        payload = {"recipient_id": str(recipient_id)}
        return await self.request("POST", "/users/@me/channels", payload=payload)
