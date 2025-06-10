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
