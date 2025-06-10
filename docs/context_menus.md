# Context Menu Commands

`disagreement` supports Discord's user and message context menu commands. Use the
`user_command` and `message_command` decorators from `ext.app_commands` to
define them.

```python
from disagreement.ext.app_commands import user_command, message_command, AppCommandContext
from disagreement.models import User, Message

@user_command(name="User Info")
async def user_info(ctx: AppCommandContext, user: User) -> None:
    await ctx.send(f"User: {user.username}#{user.discriminator}")

@message_command(name="Quote")
async def quote(ctx: AppCommandContext, message: Message) -> None:
    await ctx.send(message.content)
```

Add the commands to your client's handler and run `sync_commands()` to register
them with Discord.
