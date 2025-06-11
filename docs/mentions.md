# Controlling Mentions

The client exposes settings to control how mentions behave in outgoing messages.

## Default Allowed Mentions

Use the ``allowed_mentions`` parameter of :class:`disagreement.Client` to set a
default for all messages:

```python
client = disagreement.Client(
    token="YOUR_TOKEN",
    allowed_mentions={"parse": [], "replied_user": False},
)
```

When ``Client.send_message`` is called without an explicit ``allowed_mentions``
argument this value will be used.

## Next Steps

- [Commands](commands.md)
- [HTTP Client Options](http_client.md)
