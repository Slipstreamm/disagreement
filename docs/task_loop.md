# Task Loops

The tasks extension allows you to run functions periodically. Decorate an async function with `@tasks.loop(seconds=...)` and start it using `.start()`.

```python
from disagreement.ext import tasks

@tasks.loop(seconds=5.0)
async def announce():
    print("Hello from a loop")

announce.start()
```

Stop the loop with `.stop()` when you no longer need it.
