# Updating Presence

The `Client.change_presence` method allows you to update the bot's status and displayed activity.
Pass an :class:`~disagreement.models.Activity` (such as :class:`~disagreement.models.Game` or :class:`~disagreement.models.Streaming`) to describe what your bot is doing.

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

Example using the provided activity classes:

```python
from disagreement import Game

await client.change_presence(status="idle", activity=Game("with Discord"))
```

You can also specify a streaming URL:

```python
from disagreement import Streaming

await client.change_presence(status="online", activity=Streaming("My Stream", "https://twitch.tv/someone"))
```
