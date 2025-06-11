# disagreement/ext/app_commands/hybrid.py

from typing import Any, Callable, List, Optional

from .commands import SlashCommand
from disagreement.ext.commands.core import PrefixCommand


class HybridCommand(SlashCommand, PrefixCommand):  # Inherit from both
    """
    Represents a command that can be invoked as both a slash command
    and a traditional prefix-based command.
    """

    def __init__(self, callback: Callable[..., Any], **kwargs: Any):
        # Initialize SlashCommand part (which calls AppCommand.__init__)
        # We need to ensure 'type' is correctly passed for AppCommand
        # kwargs for SlashCommand: name, description, guild_ids, default_member_permissions, nsfw, parent, cog, etc.
        # kwargs for PrefixCommand: name, aliases, brief, description, cog

        # Pop prefix-specific args before passing to SlashCommand constructor
        prefix_aliases = kwargs.pop("aliases", [])
        prefix_brief = kwargs.pop("brief", None)
        # Description is used by both, AppCommand's constructor will handle it.
        # Name is used by both. Cog is used by both.

        # Call SlashCommand's __init__
        # This will set up name, description, callback, type=CHAT_INPUT, options, etc.
        super().__init__(callback, **kwargs)  # This is SlashCommand.__init__

        # Now, explicitly initialize the PrefixCommand parts that SlashCommand didn't cover
        # or that need specific values for the prefix version.
        # PrefixCommand.__init__(self, callback, name=self.name, aliases=prefix_aliases, brief=prefix_brief, description=self.description, cog=self.cog)
        # However, PrefixCommand.__init__ also sets self.params, which AppCommand already did.
        # We need to be careful not to re-initialize things unnecessarily or incorrectly.
        # Let's manually set the distinct attributes for the PrefixCommand aspect.

        # Attributes from PrefixCommand:
        # self.callback is already set by AppCommand
        # self.name is already set by AppCommand
        self.aliases: List[str] = (
            prefix_aliases  # This was specific to HybridCommand before, now aligns with PrefixCommand
        )
        self.brief: Optional[str] = prefix_brief
        # self.description is already set by AppCommand (SlashCommand ensures it exists)
        # self.cog is already set by AppCommand
        # self.params is already set by AppCommand

        # Ensure the MRO is handled correctly. Python's MRO (C3 linearization)
        # should call SlashCommand's __init__ then AppCommand's __init__.
        # PrefixCommand.__init__ won't be called automatically unless we explicitly call it.
        # By setting attributes directly, we avoid potential issues with multiple __init__ calls
        # if their logic overlaps too much (e.g., both trying to set self.params).

    # We might need to override invoke if the context or argument passing differs significantly
    # between app command invocation and prefix command invocation.
    # For now, SlashCommand.invoke and PrefixCommand.invoke are separate.
    # The correct one will be called depending on how the command is dispatched.
    # The AppCommandHandler will use AppCommand.invoke (via SlashCommand).
    # The prefix CommandHandler will use PrefixCommand.invoke.
    # This seems acceptable.
