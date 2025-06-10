# Task Loops

The tasks extension allows you to run functions periodically. Decorate an async function with `@tasks.loop` and start it using `.start()`.

```python
from disagreement.ext import tasks

@tasks.loop(minutes=1.0)
async def announce():
    print("Hello from a loop")

announce.start()
```

Stop the loop with `.stop()` when you no longer need it.

You can provide the interval in seconds, minutes, hours or as a `datetime.timedelta`:

```python
import datetime

@tasks.loop(delta=datetime.timedelta(seconds=30))
async def ping():
    ...
```

Handle exceptions raised by the looped coroutine using `on_error`:

```python
async def log_error(exc: Exception) -> None:
    print("Loop failed:", exc)

@tasks.loop(seconds=5.0, on_error=log_error)
async def worker():
    ...
```

You can also schedule a task at a specific time of day:

```python
from datetime import datetime, timedelta

time_to_run = (datetime.now() + timedelta(seconds=5)).time()

@tasks.loop(time_of_day=time_to_run)
async def daily_task():
    ...
```
