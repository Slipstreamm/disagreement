from collections import defaultdict
from typing import List, Optional

from ...utils import Paginator
from .core import Command, CommandContext, CommandHandler, Group


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
                if isinstance(cmd, Group):
                    await self.send_group_help(ctx, cmd)
                elif cmd:
                    description = cmd.description or cmd.brief or "No description provided."
                    await ctx.send(f"**{ctx.prefix}{cmd.name}**\n{description}")
                else:
                    lines: List[str] = []
                    for registered in handler.walk_commands():
                        brief = registered.brief or registered.description or ""
                        lines.append(f"{ctx.prefix}{registered.name} - {brief}".strip())
                    if lines:
                        await ctx.send("\n".join(lines))
                else:
                    await self.send_command_help(ctx, cmd)
            else:
                await self.send_bot_help(ctx)

        super().__init__(
            callback,
            name="help",
            brief="Show command help.",
            description="Displays help for commands.",
        )

    async def send_bot_help(self, ctx: CommandContext) -> None:
        groups = defaultdict(list)
        for cmd in dict.fromkeys(self.handler.commands.values()):
            key = cmd.cog.cog_name if cmd.cog else "No Category"
            groups[key].append(cmd)

        paginator = Paginator()
        for cog_name, cmds in groups.items():
            paginator.add_line(f"**{cog_name}**")
            for cmd in cmds:
                brief = cmd.brief or cmd.description or ""
                paginator.add_line(f"{ctx.prefix}{cmd.name} - {brief}".strip())
            paginator.add_line("")

        pages = paginator.pages
        if not pages:
            await ctx.send("No commands available.")
            return
        for page in pages:
            await ctx.send(page)

    async def send_command_help(self, ctx: CommandContext, command: Command) -> None:
        description = command.description or command.brief or "No description provided."
        await ctx.send(f"**{ctx.prefix}{command.name}**\n{description}")

    async def send_group_help(self, ctx: CommandContext, group: Group) -> None:
        paginator = Paginator()
        description = group.description or group.brief or "No description provided."
        paginator.add_line(f"**{ctx.prefix}{group.name}**\n{description}")
        if group.commands:
            for sub in dict.fromkeys(group.commands.values()):
                brief = sub.brief or sub.description or ""
                paginator.add_line(
                    f"{ctx.prefix}{group.name} {sub.name} - {brief}".strip()
                )

        for page in paginator.pages:
            await ctx.send(page)
