# Updating Presence

The `Client.change_presence` method allows you to update the bot's status and displayed activity.

## Status Strings

- `online` – show the bot as online
- `idle` – mark the bot as away
- `dnd` – do not disturb
- `invisible` – appear offline

## Activity Types

An activity dictionary must include a `name` and a `type` field. The type value corresponds to Discord's activity types:

| Type | Meaning      |
|-----:|--------------|
| `0`  | Playing      |
| `1`  | Streaming    |
| `2`  | Listening    |
| `3`  | Watching     |
| `4`  | Custom       |
| `5`  | Competing    |

Example:

```python
await client.change_presence(status="idle", activity={"name": "with Discord", "type": 0})
```
