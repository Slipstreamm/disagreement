# Events

Disagreement dispatches Gateway events to asynchronous callbacks. Handlers can be registered with `@client.event` or `client.on_event`.
Listeners may be removed later using `EventDispatcher.unregister(event_name, coro)`.

## Raw Events

Every Gateway event is also emitted with a `RAW_` prefix containing the unparsed payload. Raw events fire **before** any caching or parsing occurs.

```python
@client.on_event("RAW_MESSAGE_DELETE")
async def handle_raw_delete(payload: dict):
    print("message deleted", payload["id"])
```


## PRESENCE_UPDATE

Triggered when a user's presence changes. The callback receives a `PresenceUpdate` model.

```python
@client.event
async def on_presence_update(presence: disagreement.PresenceUpdate):
    ...
```

## TYPING_START

Dispatched when a user begins typing in a channel. The callback receives a `TypingStart` model.

```python
@client.event
async def on_typing_start(typing: disagreement.TypingStart):
    ...
```

## GUILD_MEMBER_ADD

Fired when a new member joins a guild. The callback receives a `Member` model.

```python
@client.event
async def on_guild_member_add(member: disagreement.Member):
    ...
```

## GUILD_MEMBER_REMOVE

Triggered when a member leaves or is removed from a guild. The callback
receives a `GuildMemberRemove` model.

```python
@client.event
async def on_guild_member_remove(event: disagreement.GuildMemberRemove):
    ...
```

## GUILD_BAN_ADD

Dispatched when a user is banned from a guild. The callback receives a
`GuildBanAdd` model.

```python
@client.event
async def on_guild_ban_add(event: disagreement.GuildBanAdd):
    ...
```

## GUILD_BAN_REMOVE

Dispatched when a user's ban is lifted. The callback receives a
`GuildBanRemove` model.

```python
@client.event
async def on_guild_ban_remove(event: disagreement.GuildBanRemove):
    ...
```

## CHANNEL_UPDATE

Sent when a channel's settings change. The callback receives an updated
`Channel` model.

```python
@client.event
async def on_channel_update(channel: disagreement.Channel):
    ...
```

## GUILD_ROLE_UPDATE

Emitted when a guild role is updated. The callback receives a
`GuildRoleUpdate` model.

```python
@client.event
async def on_guild_role_update(event: disagreement.GuildRoleUpdate):
    ...
```

## SHARD_CONNECT

Fired when a shard establishes its gateway connection. The callback receives a
dictionary with the shard ID.

```python
@client.event
async def on_shard_connect(info: dict):
    print("shard connected", info["shard_id"])
```

## SHARD_DISCONNECT

Emitted when a shard's gateway connection is closed. The callback receives a
dictionary with the shard ID.

```python
@client.event
async def on_shard_disconnect(info: dict):
    ...
```

## SHARD_RESUME

Sent when a shard successfully resumes after a reconnect. The callback receives
a dictionary with the shard ID.

```python
@client.event
async def on_shard_resume(info: dict):
    ...
```
