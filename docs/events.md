# Events

Disagreement dispatches Gateway events to asynchronous callbacks. Handlers can be registered with `@client.event` or `client.on_event`.
Listeners may be removed later using `EventDispatcher.unregister(event_name, coro)`.


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
