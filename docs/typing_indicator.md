# Typing Indicator

The library exposes an async context manager to send the typing indicator for a channel.

```python
import asyncio
import disagreement

client = disagreement.Client(token="YOUR_TOKEN")

async def indicate(channel_id: str):
    async with client.typing(channel_id):
        await long_running_task()
```

This uses the underlying HTTP endpoint `/channels/{channel_id}/typing`.
