# disagreement/ext/commands/help.py

from typing import List, Optional

from .core import Command, CommandContext, CommandHandler


class HelpCommand(Command):
    """Built-in command that displays help information for other commands."""

    def __init__(self, handler: CommandHandler) -> None:
        self.handler = handler

        async def callback(ctx: CommandContext, command: Optional[str] = None) -> None:
            if command:
                cmd = handler.get_command(command)
                if not cmd or cmd.name.lower() != command.lower():
                    await ctx.send(f"Command '{command}' not found.")
                    return
                description = cmd.description or cmd.brief or "No description provided."
                await ctx.send(f"**{ctx.prefix}{cmd.name}**\n{description}")
            else:
                lines: List[str] = []
                for registered in dict.fromkeys(handler.commands.values()):
                    brief = registered.brief or registered.description or ""
                    lines.append(f"{ctx.prefix}{registered.name} - {brief}".strip())
                if lines:
                    await ctx.send("\n".join(lines))
                else:
                    await ctx.send("No commands available.")

        super().__init__(
            callback,
            name="help",
            brief="Show command help.",
            description="Displays help for commands.",
        )
