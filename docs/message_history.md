# Message History

`TextChannel.history` provides an async iterator over a channel's past messages. The iterator is powered by `utils.message_pager` which handles pagination for you.

```python
channel = await client.fetch_channel(123456789012345678)
async for message in channel.history(limit=200):
    print(message.content)
```

Pass `before` or `after` to control the range of messages returned. The paginator fetches messages in batches of up to 100 until the limit is reached or Discord returns no more messages.

## Next Steps

- [Caching](caching.md)
- [Typing Indicator](typing_indicator.md)
- [Audit Logs](audit_logs.md)
- [HTTP Client Options](http_client.md)
