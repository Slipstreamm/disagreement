# Controlling Mentions

The client exposes settings to control how mentions behave in outgoing messages.

## Default Allowed Mentions

Use the ``allowed_mentions`` parameter of :class:`disagreement.Client` to set a
default for all messages:

```python
from disagreement.models import AllowedMentions
client = disagreement.Client(
    token="YOUR_TOKEN",
    allowed_mentions=AllowedMentions.none().to_dict(),
)
```

When ``Client.send_message`` or convenience methods like ``Message.reply`` and
``CommandContext.reply`` are called without an explicit ``allowed_mentions``
argument this value will be used.

``AllowedMentions`` also provides the convenience methods
``AllowedMentions.none()`` and ``AllowedMentions.all()`` to quickly create
common configurations.

## Next Steps

- [Commands](commands.md)
- [HTTP Client Options](http_client.md)
