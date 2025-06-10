# Sharding

`disagreement` supports splitting your gateway connection across multiple shards.
Use `Client` with the `shard_count` parameter when you want to control the count
manually.

`AutoShardedClient` asks Discord for the recommended number of shards at runtime
and configures the `ShardManager` automatically.

```python
import asyncio
import disagreement

bot = disagreement.AutoShardedClient(token="YOUR_TOKEN")

async def main():
    await bot.run()

asyncio.run(main())
```
