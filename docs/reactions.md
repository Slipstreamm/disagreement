# Handling Reactions

`disagreement` provides simple helpers for adding and removing message reactions.

## HTTP Methods

Use the `HTTPClient` methods directly if you need lower level control:

```python
await client._http.create_reaction(channel_id, message_id, "👍")
await client._http.delete_reaction(channel_id, message_id, "👍")
users = await client._http.get_reactions(channel_id, message_id, "👍")
```

You can also use the higher level helpers on :class:`Client`:

```python
await client.create_reaction(channel_id, message_id, "👍")
await client.delete_reaction(channel_id, message_id, "👍")
users = await client.get_reactions(channel_id, message_id, "👍")
```

## Reaction Events

Register listeners for `MESSAGE_REACTION_ADD` and `MESSAGE_REACTION_REMOVE`.
Each listener receives a `Reaction` model instance.

```python
@client.on_event("MESSAGE_REACTION_ADD")
async def on_reaction(reaction: disagreement.Reaction):
    print(f"{reaction.user_id} reacted with {reaction.emoji}")
```
