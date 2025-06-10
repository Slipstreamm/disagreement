import asyncio
from typing import Any, Awaitable, Callable, Optional

__all__ = ["loop", "Task"]


class Task:
    """Simple repeating task."""

    def __init__(self, coro: Callable[..., Awaitable[Any]], *, seconds: float) -> None:
        self._coro = coro
        self._seconds = float(seconds)
        self._task: Optional[asyncio.Task[None]] = None

    async def _run(self, *args: Any, **kwargs: Any) -> None:
        try:
            while True:
                await self._coro(*args, **kwargs)
                await asyncio.sleep(self._seconds)
        except asyncio.CancelledError:
            pass

    def start(self, *args: Any, **kwargs: Any) -> asyncio.Task[None]:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run(*args, **kwargs))
        return self._task

    def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()


class _Loop:
    def __init__(self, func: Callable[..., Awaitable[Any]], seconds: float) -> None:
        self.func = func
        self.seconds = seconds
        self._task: Optional[Task] = None
        self._owner: Any = None

    def __get__(self, obj: Any, objtype: Any) -> "_BoundLoop":
        return _BoundLoop(self, obj)

    def _coro(self, *args: Any, **kwargs: Any) -> Awaitable[Any]:
        if self._owner is None:
            return self.func(*args, **kwargs)
        return self.func(self._owner, *args, **kwargs)

    def start(self, *args: Any, **kwargs: Any) -> asyncio.Task[None]:
        self._task = Task(self._coro, seconds=self.seconds)
        return self._task.start(*args, **kwargs)

    def stop(self) -> None:
        if self._task is not None:
            self._task.stop()

    @property
    def running(self) -> bool:
        return self._task.running if self._task else False


class _BoundLoop:
    def __init__(self, parent: _Loop, owner: Any) -> None:
        self._parent = parent
        self._owner = owner

    def start(self, *args: Any, **kwargs: Any) -> asyncio.Task[None]:
        self._parent._owner = self._owner
        return self._parent.start(*args, **kwargs)

    def stop(self) -> None:
        self._parent.stop()

    @property
    def running(self) -> bool:
        return self._parent.running


def loop(*, seconds: float) -> Callable[[Callable[..., Awaitable[Any]]], _Loop]:
    """Decorator to create a looping task."""

    def decorator(func: Callable[..., Awaitable[Any]]) -> _Loop:
        return _Loop(func, seconds)

    return decorator
