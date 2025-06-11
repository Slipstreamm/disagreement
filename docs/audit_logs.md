# Audit Logs

`Client.fetch_audit_logs` provides an async iterator over a guild's audit log entries.

```python
async for entry in client.fetch_audit_logs(guild_id, limit=100):
    print(entry.action_type, entry.user_id)
```

Discord imposes stricter rate limits on this endpoint compared to other REST calls. Avoid polling too frequently or you may hit a `429` response.

## Next Steps

- [Caching](caching.md)
- [Message History](message_history.md)
