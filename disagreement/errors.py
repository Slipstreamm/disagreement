"""
Custom exceptions for the Disagreement library.
"""

from typing import Optional, Any


class DisagreementException(Exception):
    """Base exception class for all errors raised by this library."""

    pass


class HTTPException(DisagreementException):
    """Exception raised for HTTP-related errors.

    Attributes:
        response: The aiohttp response object, if available.
        status: The HTTP status code.
        text: The response text, if available.
        error_code: Discord specific error code, if available.
    """

    def __init__(
        self, response=None, message=None, *, status=None, text=None, error_code=None
    ):
        self.response = response
        self.status = status or (response.status if response else None)
        self.text = text or (
            response.text if response else None
        )  # Or await response.text() if in async context
        self.error_code = error_code

        full_message = f"HTTP {self.status}"
        if message:
            full_message += f": {message}"
        elif self.text:
            full_message += f": {self.text}"
        if self.error_code:
            full_message += f" (Discord Error Code: {self.error_code})"

        super().__init__(full_message)


class GatewayException(DisagreementException):
    """Exception raised for errors related to the Discord Gateway connection or protocol."""

    pass


class AuthenticationError(DisagreementException):
    """Exception raised for authentication failures (e.g., invalid token)."""

    pass


class RateLimitError(HTTPException):
    """
    Exception raised when a rate limit is encountered.

    Attributes:
        retry_after (float): The number of seconds to wait before retrying.
        is_global (bool): Whether this is a global rate limit.
    """

    def __init__(
        self, response, message=None, *, retry_after: float, is_global: bool = False
    ):
        self.retry_after = retry_after
        self.is_global = is_global
        super().__init__(
            response,
            message
            or f"Rate limited. Retry after: {retry_after}s. Global: {is_global}",
        )


# Specific HTTP error exceptions


class NotFound(HTTPException):
    """Raised for 404 Not Found errors."""

    pass


class Forbidden(HTTPException):
    """Raised for 403 Forbidden errors."""

    pass


class GeneralError(HTTPException):
    """General error (such as a malformed request body, amongst other things) (Code: 0)"""

    pass


class UnknownAccount(HTTPException):
    """Unknown account (Code: 10001)"""

    pass


class UnknownApplication(HTTPException):
    """Unknown application (Code: 10002)"""

    pass


class UnknownChannel(HTTPException):
    """Unknown channel (Code: 10003)"""

    pass


class UnknownGuild(HTTPException):
    """Unknown guild (Code: 10004)"""

    pass


class UnknownIntegration(HTTPException):
    """Unknown integration (Code: 10005)"""

    pass


class UnknownInvite(HTTPException):
    """Unknown invite (Code: 10006)"""

    pass


class UnknownMember(HTTPException):
    """Unknown member (Code: 10007)"""

    pass


class UnknownMessage(HTTPException):
    """Unknown message (Code: 10008)"""

    pass


class UnknownPermissionOverwrite(HTTPException):
    """Unknown permission overwrite (Code: 10009)"""

    pass


class UnknownProvider(HTTPException):
    """Unknown provider (Code: 10010)"""

    pass


class UnknownRole(HTTPException):
    """Unknown role (Code: 10011)"""

    pass


class UnknownToken(HTTPException):
    """Unknown token (Code: 10012)"""

    pass


class UnknownUser(HTTPException):
    """Unknown user (Code: 10013)"""

    pass


class UnknownEmoji(HTTPException):
    """Unknown emoji (Code: 10014)"""

    pass


class UnknownWebhook(HTTPException):
    """Unknown webhook (Code: 10015)"""

    pass


class UnknownWebhookService(HTTPException):
    """Unknown webhook service (Code: 10016)"""

    pass


class UnknownSession(HTTPException):
    """Unknown session (Code: 10020)"""

    pass


class UnknownAsset(HTTPException):
    """Unknown Asset (Code: 10021)"""

    pass


class UnknownBan(HTTPException):
    """Unknown ban (Code: 10026)"""

    pass


class UnknownSKU(HTTPException):
    """Unknown SKU (Code: 10027)"""

    pass


class UnknownStoreListing(HTTPException):
    """Unknown Store Listing (Code: 10028)"""

    pass


class UnknownEntitlement(HTTPException):
    """Unknown entitlement (Code: 10029)"""

    pass


class UnknownBuild(HTTPException):
    """Unknown build (Code: 10030)"""

    pass


class UnknownLobby(HTTPException):
    """Unknown lobby (Code: 10031)"""

    pass


class UnknownBranch(HTTPException):
    """Unknown branch (Code: 10032)"""

    pass


class UnknownStoreDirectoryLayout(HTTPException):
    """Unknown store directory layout (Code: 10033)"""

    pass


class UnknownRedistributable(HTTPException):
    """Unknown redistributable (Code: 10036)"""

    pass


class UnknownGiftCode(HTTPException):
    """Unknown gift code (Code: 10038)"""

    pass


class UnknownStream(HTTPException):
    """Unknown stream (Code: 10049)"""

    pass


class UnknownPremiumServerSubscribeCooldown(HTTPException):
    """Unknown premium server subscribe cooldown (Code: 10050)"""

    pass


class UnknownGuildTemplate(HTTPException):
    """Unknown guild template (Code: 10057)"""

    pass


class UnknownDiscoverableServerCategory(HTTPException):
    """Unknown discoverable server category (Code: 10059)"""

    pass


class UnknownSticker(HTTPException):
    """Unknown sticker (Code: 10060)"""

    pass


class UnknownStickerPack(HTTPException):
    """Unknown sticker pack (Code: 10061)"""

    pass


class UnknownInteraction(HTTPException):
    """Unknown interaction (Code: 10062)"""

    pass


class UnknownApplicationCommand(HTTPException):
    """Unknown application command (Code: 10063)"""

    pass


class UnknownVoiceState(HTTPException):
    """Unknown voice state (Code: 10065)"""

    pass


class UnknownApplicationCommandPermissions(HTTPException):
    """Unknown application command permissions (Code: 10066)"""

    pass


class UnknownStageInstance(HTTPException):
    """Unknown Stage Instance (Code: 10067)"""

    pass


class UnknownGuildMemberVerificationForm(HTTPException):
    """Unknown Guild Member Verification Form (Code: 10068)"""

    pass


class UnknownGuildWelcomeScreen(HTTPException):
    """Unknown Guild Welcome Screen (Code: 10069)"""

    pass


class UnknownGuildScheduledEvent(HTTPException):
    """Unknown Guild Scheduled Event (Code: 10070)"""

    pass


class UnknownGuildScheduledEventUser(HTTPException):
    """Unknown Guild Scheduled Event User (Code: 10071)"""

    pass


class UnknownTag(HTTPException):
    """Unknown Tag (Code: 10087)"""

    pass


class UnknownSound(HTTPException):
    """Unknown sound (Code: 10097)"""

    pass


class BotsCannotUseThisEndpoint(HTTPException):
    """Bots cannot use this endpoint (Code: 20001)"""

    pass


class OnlyBotsCanUseThisEndpoint(HTTPException):
    """Only bots can use this endpoint (Code: 20002)"""

    pass


class ExplicitContentCannotBeSentToTheDesiredRecipients(HTTPException):
    """Explicit content cannot be sent to the desired recipient(s) (Code: 20009)"""

    pass


class NotAuthorizedToPerformThisActionOnThisApplication(HTTPException):
    """You are not authorized to perform this action on this application (Code: 20012)"""

    pass


class ActionCannotBePerformedDueToSlowmodeRateLimit(HTTPException):
    """This action cannot be performed due to slowmode rate limit (Code: 20016)"""

    pass


class OnlyTheOwnerOfThisAccountCanPerformThisAction(HTTPException):
    """Only the owner of this account can perform this action (Code: 20018)"""

    pass


class MessageCannotBeEditedDueToAnnouncementRateLimits(HTTPException):
    """This message cannot be edited due to announcement rate limits (Code: 20022)"""

    pass


class UnderMinimumAge(HTTPException):
    """Under minimum age (Code: 20024)"""

    pass


class ChannelHitWriteRateLimit(HTTPException):
    """The channel you are writing has hit the write rate limit (Code: 20028)"""

    pass


class ServerHitWriteRateLimit(HTTPException):
    """The write action you are performing on the server has hit the write rate limit (Code: 20029)"""

    pass


class DisallowedWordsInStageTopicOrNames(HTTPException):
    """Your Stage topic, server name, server description, or channel names contain words that are not allowed (Code: 20031)"""

    pass


class GuildPremiumSubscriptionLevelTooLow(HTTPException):
    """Guild premium subscription level too low (Code: 20035)"""

    pass


class MaximumNumberOfGuildsReached(HTTPException):
    """Maximum number of guilds reached (100) (Code: 30001)"""

    pass


class MaximumNumberOfFriendsReached(HTTPException):
    """Maximum number of friends reached (1000) (Code: 30002)"""

    pass


class MaximumNumberOfPinsReached(HTTPException):
    """Maximum number of pins reached for the channel (50) (Code: 30003)"""

    pass


class MaximumNumberOfRecipientsReached(HTTPException):
    """Maximum number of recipients reached (10) (Code: 30004)"""

    pass


class MaximumNumberOfGuildRolesReached(HTTPException):
    """Maximum number of guild roles reached (250) (Code: 30005)"""

    pass


class MaximumNumberOfWebhooksReached(HTTPException):
    """Maximum number of webhooks reached (15) (Code: 30007)"""

    pass


class MaximumNumberOfEmojisReached(HTTPException):
    """Maximum number of emojis reached (Code: 30008)"""

    pass


class MaximumNumberOfReactionsReached(HTTPException):
    """Maximum number of reactions reached (20) (Code: 30010)"""

    pass


class MaximumNumberOfGroupDMsReached(HTTPException):
    """Maximum number of group DMs reached (10) (Code: 30011)"""

    pass


class MaximumNumberOfGuildChannelsReached(HTTPException):
    """Maximum number of guild channels reached (500) (Code: 30013)"""

    pass


class MaximumNumberOfAttachmentsInAMessageReached(HTTPException):
    """Maximum number of attachments in a message reached (10) (Code: 30015)"""

    pass


class MaximumNumberOfInvitesReached(HTTPException):
    """Maximum number of invites reached (1000) (Code: 30016)"""

    pass


class MaximumNumberOfAnimatedEmojisReached(HTTPException):
    """Maximum number of animated emojis reached (Code: 30018)"""

    pass


class MaximumNumberOfServerMembersReached(HTTPException):
    """Maximum number of server members reached (Code: 30019)"""

    pass


class MaximumNumberOfServerCategoriesReached(HTTPException):
    """Maximum number of server categories has been reached (5) (Code: 30030)"""

    pass


class GuildAlreadyHasATemplate(HTTPException):
    """Guild already has a template (Code: 30031)"""

    pass


class MaximumNumberOfApplicationCommandsReached(HTTPException):
    """Maximum number of application commands reached (Code: 30032)"""

    pass


class MaximumNumberOfThreadParticipantsReached(HTTPException):
    """Maximum number of thread participants has been reached (1000) (Code: 30033)"""

    pass


class MaximumNumberOfDailyApplicationCommandCreatesReached(HTTPException):
    """Maximum number of daily application command creates has been reached (200) (Code: 30034)"""

    pass


class MaximumNumberOfBansForNonGuildMembersExceeded(HTTPException):
    """Maximum number of bans for non-guild members have been exceeded (Code: 30035)"""

    pass


class MaximumNumberOfBansFetchesReached(HTTPException):
    """Maximum number of bans fetches has been reached (Code: 30037)"""

    pass


class MaximumNumberOfUncompletedGuildScheduledEventsReached(HTTPException):
    """Maximum number of uncompleted guild scheduled events reached (100) (Code: 30038)"""

    pass


class MaximumNumberOfStickersReached(HTTPException):
    """Maximum number of stickers reached (Code: 30039)"""

    pass


class MaximumNumberOfPruneRequestsReached(HTTPException):
    """Maximum number of prune requests has been reached. Try again later (Code: 30040)"""

    pass


class MaximumNumberOfGuildWidgetSettingsUpdatesReached(HTTPException):
    """Maximum number of guild widget settings updates has been reached. Try again later (Code: 30042)"""

    pass


class MaximumNumberOfSoundboardSoundsReached(HTTPException):
    """Maximum number of soundboard sounds reached (Code: 30045)"""

    pass


class MaximumNumberOfEditsToMessagesOlderThan1HourReached(HTTPException):
    """Maximum number of edits to messages older than 1 hour reached. Try again later (Code: 30046)"""

    pass


class MaximumNumberOfPinnedThreadsInAForumChannelReached(HTTPException):
    """Maximum number of pinned threads in a forum channel has been reached (Code: 30047)"""

    pass


class MaximumNumberOfTagsInAForumChannelReached(HTTPException):
    """Maximum number of tags in a forum channel has been reached (Code: 30048)"""

    pass


class BitrateIsTooHighForChannelOfThisType(HTTPException):
    """Bitrate is too high for channel of this type (Code: 30052)"""

    pass


class MaximumNumberOfPremiumEmojisReached(HTTPException):
    """Maximum number of premium emojis reached (25) (Code: 30056)"""

    pass


class MaximumNumberOfWebhooksPerGuildReached(HTTPException):
    """Maximum number of webhooks per guild reached (1000) (Code: 30058)"""

    pass


class MaximumNumberOfChannelPermissionOverwritesReached(HTTPException):
    """Maximum number of channel permission overwrites reached (1000) (Code: 30061)"""

    pass


class TheChannelsForThisGuildAreTooLarge(HTTPException):
    """The channels for this guild are too large (Code: 30061)"""

    pass


class Unauthorized(HTTPException):
    """Unauthorized. Provide a valid token and try again (Code: 40001)"""

    pass


class YouNeedToVerifyYourAccount(HTTPException):
    """You need to verify your account in order to perform this action (Code: 40002)"""

    pass


class YouAreOpeningDirectMessagesTooFast(HTTPException):
    """You are opening direct messages too fast (Code: 40003)"""

    pass


class SendMessagesHasBeenTemporarilyDisabled(HTTPException):
    """Send messages has been temporarily disabled (Code: 40004)"""

    pass


class RequestEntityTooLarge(HTTPException):
    """Request entity too large. Try sending something smaller in size (Code: 40005)"""

    pass


class ThisFeatureHasBeenTemporarilyDisabledServerSide(HTTPException):
    """This feature has been temporarily disabled server-side (Code: 40006)"""

    pass


class TheUserIsBannedFromThisGuild(HTTPException):
    """The user is banned from this guild (Code: 40007)"""

    pass


class ConnectionHasBeenRevoked(HTTPException):
    """Connection has been revoked (Code: 40012)"""

    pass


class OnlyConsumableSKUsCanBeConsumed(HTTPException):
    """Only consumable SKUs can be consumed (Code: 40018)"""

    pass


class YouCanOnlyDeleteSandboxEntitlements(HTTPException):
    """You can only delete sandbox entitlements. (Code: 40019)"""

    pass


class TargetUserIsNotConnectedToVoice(HTTPException):
    """Target user is not connected to voice (Code: 40032)"""

    pass


class ThisMessageHasAlreadyBeenCrossposted(HTTPException):
    """This message has already been crossposted (Code: 40033)"""

    pass


class AnApplicationCommandWithThatNameAlreadyExists(HTTPException):
    """An application command with that name already exists (Code: 40041)"""

    pass


class ApplicationInteractionFailedToSend(HTTPException):
    """Application interaction failed to send (Code: 40043)"""

    pass


class CannotSendAMessageInAForumChannel(HTTPException):
    """Cannot send a message in a forum channel (Code: 40058)"""

    pass


class InteractionHasAlreadyBeenAcknowledged(HTTPException):
    """Interaction has already been acknowledged (Code: 40060)"""

    pass


class TagNamesMustBeUnique(HTTPException):
    """Tag names must be unique (Code: 40061)"""

    pass


class ServiceResourceIsBeingRateLimited(HTTPException):
    """Service resource is being rate limited (Code: 40062)"""

    pass


class ThereAreNoTagsAvailableThatCanBeSetByNonModerators(HTTPException):
    """There are no tags available that can be set by non-moderators (Code: 40066)"""

    pass


class ATagIsRequiredToCreateAForumPostInThisChannel(HTTPException):
    """A tag is required to create a forum post in this channel (Code: 40067)"""

    pass


class AnEntitlementHasAlreadyBeenGrantedForThisResource(HTTPException):
    """An entitlement has already been granted for this resource (Code: 40074)"""

    pass


class ThisInteractionHasHitTheMaximumNumberOfFollowUpMessages(HTTPException):
    """This interaction has hit the maximum number of follow up messages (Code: 40094)"""

    pass


class CloudflareIsBlockingYourRequest(HTTPException):
    """Cloudflare is blocking your request. This can often be resolved by setting a proper User Agent (Code: 40333)"""

    pass


class MissingAccess(HTTPException):
    """Missing access (Code: 50001)"""

    pass


class InvalidAccountType(HTTPException):
    """Invalid account type (Code: 50002)"""

    pass


class CannotExecuteActionOnADMChannel(HTTPException):
    """Cannot execute action on a DM channel (Code: 50003)"""

    pass


class GuildWidgetDisabled(HTTPException):
    """Guild widget disabled (Code: 50004)"""

    pass


class CannotEditAMessageAuthoredByAnotherUser(HTTPException):
    """Cannot edit a message authored by another user (Code: 50005)"""

    pass


class CannotSendAnEmptyMessage(HTTPException):
    """Cannot send an empty message (Code: 50006)"""

    pass


class CannotSendMessagesToThisUser(HTTPException):
    """Cannot send messages to this user (Code: 50007)"""

    pass


class CannotSendMessagesInANonTextChannel(HTTPException):
    """Cannot send messages in a non-text channel (Code: 50008)"""

    pass


class ChannelVerificationLevelIsTooHighForYouToGainAccess(HTTPException):
    """Channel verification level is too high for you to gain access (Code: 50009)"""

    pass


class OAuth2ApplicationDoesNotHaveABot(HTTPException):
    """OAuth2 application does not have a bot (Code: 50010)"""

    pass


class OAuth2ApplicationLimitReached(HTTPException):
    """OAuth2 application limit reached (Code: 50011)"""

    pass


class InvalidOAuth2State(HTTPException):
    """Invalid OAuth2 state (Code: 50012)"""

    pass


class YouLackPermissionsToPerformThatAction(HTTPException):
    """You lack permissions to perform that action (Code: 50013)"""

    pass


class InvalidAuthenticationTokenProvided(HTTPException):
    """Invalid authentication token provided (Code: 50014)"""

    pass


class NoteWasTooLong(HTTPException):
    """Note was too long (Code: 50015)"""

    pass


class ProvidedTooFewOrTooManyMessagesToDelete(HTTPException):
    """Provided too few or too many messages to delete. Must provide at least 2 and fewer than 100 messages to delete (Code: 50016)"""

    pass


class InvalidMFALevel(HTTPException):
    """Invalid MFA Level (Code: 50017)"""

    pass


class AMessageCanOnlyBePinnedToTheChannelItWasSentIn(HTTPException):
    """A message can only be pinned to the channel it was sent in (Code: 50019)"""

    pass


class InviteCodeWasEitherInvalidOrTaken(HTTPException):
    """Invite code was either invalid or taken (Code: 50020)"""

    pass


class CannotExecuteActionOnASystemMessage(HTTPException):
    """Cannot execute action on a system message (Code: 50021)"""

    pass


class CannotExecuteActionOnThisChannelType(HTTPException):
    """Cannot execute action on this channel type (Code: 50024)"""

    pass


class InvalidOAuth2AccessTokenProvided(HTTPException):
    """Invalid OAuth2 access token provided (Code: 50025)"""

    pass


class MissingRequiredOAuth2Scope(HTTPException):
    """Missing required OAuth2 scope (Code: 50026)"""

    pass


class InvalidWebhookTokenProvided(HTTPException):
    """Invalid webhook token provided (Code: 50027)"""

    pass


class InvalidRole(HTTPException):
    """Invalid role (Code: 50028)"""

    pass


class InvalidRecipients(HTTPException):
    """Invalid Recipient(s) (Code: 50033)"""

    pass


class AMessageProvidedWasTooOldToBulkDelete(HTTPException):
    """A message provided was too old to bulk delete (Code: 50034)"""

    pass


class InvalidFormBody(HTTPException):
    """Invalid form body (returned for both application/json and multipart/form-data bodies), or invalid Content-Type provided (Code: 50035)"""

    pass


class AnInviteWasAcceptedToAGuildTheApplicationBotIsNotIn(HTTPException):
    """An invite was accepted to a guild the application's bot is not in (Code: 50036)"""

    pass


class InvalidActivityAction(HTTPException):
    """Invalid Activity Action (Code: 50039)"""

    pass


class InvalidAPIVersionProvided(HTTPException):
    """Invalid API version provided (Code: 50041)"""

    pass


class FileUploadedExceedsTheMaximumSize(HTTPException):
    """File uploaded exceeds the maximum size (Code: 50045)"""

    pass


class InvalidFileUploaded(HTTPException):
    """Invalid file uploaded (Code: 50046)"""

    pass


class CannotSelfRedeemThisGift(HTTPException):
    """Cannot self-redeem this gift (Code: 50054)"""

    pass


class InvalidGuild(HTTPException):
    """Invalid Guild (Code: 50055)"""

    pass


class InvalidSKU(HTTPException):
    """Invalid SKU (Code: 50057)"""

    pass


class InvalidRequestOrigin(HTTPException):
    """Invalid request origin (Code: 50067)"""

    pass


class InvalidMessageType(HTTPException):
    """Invalid message type (Code: 50068)"""

    pass


class PaymentSourceRequiredToRedeemGift(HTTPException):
    """Payment source required to redeem gift (Code: 50070)"""

    pass


class CannotModifyASystemWebhook(HTTPException):
    """Cannot modify a system webhook (Code: 50073)"""

    pass


class CannotDeleteAChannelRequiredForCommunityGuilds(HTTPException):
    """Cannot delete a channel required for Community guilds (Code: 50074)"""

    pass


class CannotEditStickersWithinAMessage(HTTPException):
    """Cannot edit stickers within a message (Code: 50080)"""

    pass


class InvalidStickerSent(HTTPException):
    """Invalid sticker sent (Code: 50081)"""

    pass


class TriedToPerformAnOperationOnAnArchivedThread(HTTPException):
    """Tried to perform an operation on an archived thread, such as editing a message or adding a user to the thread (Code: 50083)"""

    pass


class InvalidThreadNotificationSettings(HTTPException):
    """Invalid thread notification settings (Code: 50085)"""

    pass


class BeforeValueIsEarlierThanTheThreadCreationDate(HTTPException):
    """before value is earlier than the thread creation date (Code: 50086)"""

    pass


class CommunityServerChannelsMustBeTextChannels(HTTPException):
    """Community server channels must be text channels (Code: 50086)"""

    pass


class TheEntityTypeOfTheEventIsDifferentFromTheEntityYouAreTryingToStartTheEventFor(
    HTTPException
):
    """The entity type of the event is different from the entity you are trying to start the event for (Code: 50091)"""

    pass


class ThisServerIsNotAvailableInYourLocation(HTTPException):
    """This server is not available in your location (Code: 50095)"""

    pass


class ThisServerNeedsMonetizationEnabledInOrderToPerformThisAction(HTTPException):
    """This server needs monetization enabled in order to perform this action (Code: 50097)"""

    pass


class ThisServerNeedsMoreBoostsToPerformThisAction(HTTPException):
    """This server needs more boosts to perform this action (Code: 50101)"""

    pass


class TheRequestBodyContainsInvalidJSON(HTTPException):
    """The request body contains invalid JSON. (Code: 50109)"""

    pass


class TheProvidedFileIsInvalid(HTTPException):
    """The provided file is invalid. (Code: 50110)"""

    pass


class TheProvidedFileTypeIsInvalid(HTTPException):
    """The provided file type is invalid. (Code: 50123)"""

    pass


class TheProvidedFileDurationExceedsMaximumOf52Seconds(HTTPException):
    """The provided file duration exceeds maximum of 5.2 seconds. (Code: 50124)"""

    pass


class OwnerCannotBePendingMember(HTTPException):
    """Owner cannot be pending member (Code: 50131)"""

    pass


class OwnershipCannotBeTransferredToABotUser(HTTPException):
    """Ownership cannot be transferred to a bot user (Code: 50132)"""

    pass


class FailedToResizeAssetBelowTheMaximumSize(HTTPException):
    """Failed to resize asset below the maximum size: 262144 (Code: 50138)"""

    pass


class CannotMixSubscriptionAndNonSubscriptionRolesForAnEmoji(HTTPException):
    """Cannot mix subscription and non subscription roles for an emoji (Code: 50144)"""

    pass


class CannotConvertBetweenPremiumEmojiAndNormalEmoji(HTTPException):
    """Cannot convert between premium emoji and normal emoji (Code: 50145)"""

    pass


class UploadedFileNotFound(HTTPException):
    """Uploaded file not found. (Code: 50146)"""

    pass


class TheSpecifiedEmojiIsInvalid(HTTPException):
    """The specified emoji is invalid (Code: 50151)"""

    pass


class VoiceMessagesDoNotSupportAdditionalContent(HTTPException):
    """Voice messages do not support additional content. (Code: 50159)"""

    pass


class VoiceMessagesMustHaveASingleAudioAttachment(HTTPException):
    """Voice messages must have a single audio attachment. (Code: 50160)"""

    pass


class VoiceMessagesMustHaveSupportingMetadata(HTTPException):
    """Voice messages must have supporting metadata. (Code: 50161)"""

    pass


class VoiceMessagesCannotBeEdited(HTTPException):
    """Voice messages cannot be edited. (Code: 50162)"""

    pass


class CannotDeleteGuildSubscriptionIntegration(HTTPException):
    """Cannot delete guild subscription integration (Code: 50163)"""

    pass


class YouCannotSendVoiceMessagesInThisChannel(HTTPException):
    """You cannot send voice messages in this channel. (Code: 50173)"""

    pass


class TheUserAccountMustFirstBeVerified(HTTPException):
    """The user account must first be verified (Code: 50178)"""

    pass


class TheProvidedFileDoesNotHaveAValidDuration(HTTPException):
    """The provided file does not have a valid duration. (Code: 50192)"""

    pass


class YouDoNotHavePermissionToSendThisSticker(HTTPException):
    """You do not have permission to send this sticker. (Code: 50600)"""

    pass


class TwoFactorIsRequiredForThisOperation(HTTPException):
    """Two factor is required for this operation (Code: 60003)"""

    pass


class NoUsersWithDiscordTagExist(HTTPException):
    """No users with DiscordTag exist (Code: 80004)"""

    pass


class ReactionWasBlocked(HTTPException):
    """Reaction was blocked (Code: 90001)"""

    pass


class UserCannotUseBurstReactions(HTTPException):
    """User cannot use burst reactions (Code: 90002)"""

    pass


class ApplicationNotYetAvailable(HTTPException):
    """Application not yet available. Try again later (Code: 110001)"""

    pass


class APIResourceIsCurrentlyOverloaded(HTTPException):
    """API resource is currently overloaded. Try again a little later (Code: 130000)"""

    pass


class TheStageIsAlreadyOpen(HTTPException):
    """The Stage is already open (Code: 150006)"""

    pass


class CannotReplyWithoutPermissionToReadMessageHistory(HTTPException):
    """Cannot reply without permission to read message history (Code: 160002)"""

    pass


class AThreadHasAlreadyBeenCreatedForThisMessage(HTTPException):
    """A thread has already been created for this message (Code: 160004)"""

    pass


class ThreadIsLocked(HTTPException):
    """Thread is locked (Code: 160005)"""

    pass


class MaximumNumberOfActiveThreadsReached(HTTPException):
    """Maximum number of active threads reached (Code: 160006)"""

    pass


class MaximumNumberOfActiveAnnouncementThreadsReached(HTTPException):
    """Maximum number of active announcement threads reached (Code: 160007)"""

    pass


class InvalidJSONForUploadedLottieFile(HTTPException):
    """Invalid JSON for uploaded Lottie file (Code: 170001)"""

    pass


class UploadedLottiesCannotContainRasterizedImages(HTTPException):
    """Uploaded Lotties cannot contain rasterized images such as PNG or JPEG (Code: 170002)"""

    pass


class StickerMaximumFramerateExceeded(HTTPException):
    """Sticker maximum framerate exceeded (Code: 170003)"""

    pass


class StickerFrameCountExceedsMaximumOf1000Frames(HTTPException):
    """Sticker frame count exceeds maximum of 1000 frames (Code: 170004)"""

    pass


class LottieAnimationMaximumDimensionsExceeded(HTTPException):
    """Lottie animation maximum dimensions exceeded (Code: 170005)"""

    pass


class StickerFrameRateIsEitherTooSmallOrTooLarge(HTTPException):
    """Sticker frame rate is either too small or too large (Code: 170006)"""

    pass


class StickerAnimationDurationExceedsMaximumOf5Seconds(HTTPException):
    """Sticker animation duration exceeds maximum of 5 seconds (Code: 170007)"""

    pass


class CannotUpdateAFinishedEvent(HTTPException):
    """Cannot update a finished event (Code: 180000)"""

    pass


class FailedToCreateStageNeededForStageEvent(HTTPException):
    """Failed to create stage needed for stage event (Code: 180002)"""

    pass


class MessageWasBlockedByAutomaticModeration(HTTPException):
    """Message was blocked by automatic moderation (Code: 200000)"""

    pass


class TitleWasBlockedByAutomaticModeration(HTTPException):
    """Title was blocked by automatic moderation (Code: 200001)"""

    pass


class WebhooksPostedToForumChannelsMustHaveAThreadNameOrThreadId(HTTPException):
    """Webhooks posted to forum channels must have a thread_name or thread_id (Code: 220001)"""

    pass


class WebhooksPostedToForumChannelsCannotHaveBothAThreadNameAndThreadId(HTTPException):
    """Webhooks posted to forum channels cannot have both a thread_name and thread_id (Code: 220002)"""

    pass


class WebhooksCanOnlyCreateThreadsInForumChannels(HTTPException):
    """Webhooks can only create threads in forum channels (Code: 220003)"""

    pass


class WebhookServicesCannotBeUsedInForumChannels(HTTPException):
    """Webhook services cannot be used in forum channels (Code: 220004)"""

    pass


class MessageBlockedByHarmfulLinksFilter(HTTPException):
    """Message blocked by harmful links filter (Code: 240000)"""

    pass


class CannotEnableOnboardingRequirementsAreNotMet(HTTPException):
    """Cannot enable onboarding, requirements are not met (Code: 350000)"""

    pass


class CannotUpdateOnboardingWhileBelowRequirements(HTTPException):
    """Cannot update onboarding while below requirements (Code: 350001)"""

    pass


class FailedToBanUsers(HTTPException):
    """Failed to ban users (Code: 500000)"""

    pass


class PollVotingBlocked(HTTPException):
    """Poll voting blocked (Code: 520000)"""

    pass


class PollExpired(HTTPException):
    """Poll expired (Code: 520001)"""

    pass


class InvalidChannelTypeForPollCreation(HTTPException):
    """Invalid channel type for poll creation (Code: 520002)"""

    pass


class CannotEditAPollMessage(HTTPException):
    """Cannot edit a poll message (Code: 520003)"""

    pass


class CannotUseAnEmojiIncludedWithThePoll(HTTPException):
    """Cannot use an emoji included with the poll (Code: 520004)"""

    pass


class CannotExpireANonPollMessage(HTTPException):
    """Cannot expire a non-poll message (Code: 520006)"""

    pass


class AppCommandError(DisagreementException):
    """Base exception for application command related errors."""

    pass


class AppCommandOptionConversionError(AppCommandError):
    """Exception raised when an application command option fails to convert."""

    def __init__(
        self,
        message: str,
        option_name: Optional[str] = None,
        original_value: Any = None,
    ):
        self.option_name = option_name
        self.original_value = original_value
        full_message = message
        if option_name:
            full_message = f"Failed to convert option '{option_name}': {message}"
        if original_value is not None:
            full_message += f" (Original value: '{original_value}')"
        super().__init__(full_message)
