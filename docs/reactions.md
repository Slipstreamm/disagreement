# Handling Reactions

`disagreement` provides several ways to add, remove, and listen for message reactions.

## Adding & Removing Reactions

The easiest way to add a reaction is to use the helper method on a `Message` object. This is often done within a command context.

```python
# Inside a command function:
# ctx is a commands.CommandContext object
await ctx.message.add_reaction("👍")
```

You can also remove your own reactions.

```python
await ctx.message.remove_reaction("👍", client.user)
```

## Low-Level Control

For more direct control, you can use methods on the `Client` or `HTTPClient` if you have the channel and message IDs.

```python
# Using the client helper
await client.create_reaction(channel_id, message_id, "👍")

# Using the raw HTTP method
await client._http.create_reaction(channel_id, message_id, "👍")
```

Similarly, you can delete reactions and get a list of users who reacted.

```python
# Delete a specific user's reaction
await client.delete_reaction(channel_id, message_id, "👍", user_id)

# Get users who reacted with an emoji
users = await client.get_reactions(channel_id, message_id, "👍")
```

## Reaction Events

Your bot can listen for reaction events by using the `@client.on_event` decorator. The two main events are `MESSAGE_REACTION_ADD` and `MESSAGE_REACTION_REMOVE`.

The event handlers for these events receive both a `Reaction` object and the `User` or `Member` who triggered the event.

```python
import disagreement
from disagreement.models import Reaction, User, Member

@client.on_event("MESSAGE_REACTION_ADD")
async def on_reaction_add(reaction: Reaction, user: User | Member):
    # Ignore reactions from the bot itself
    if client.user and user.id == client.user.id:
        return
    print(f"{user.username} reacted to message {reaction.message_id} with {reaction.emoji}")

@client.on_event("MESSAGE_REACTION_REMOVE")
async def on_reaction_remove(reaction: Reaction, user: User | Member):
    print(f"{user.username} removed their {reaction.emoji} reaction from message {reaction.message_id}")
