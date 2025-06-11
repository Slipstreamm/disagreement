import asyncio
import datetime
from typing import Any, Awaitable, Callable, Optional

__all__ = ["loop", "Task"]


class Task:
    """Simple repeating task."""

    def __init__(
        self,
        coro: Callable[..., Awaitable[Any]],
        *,
        seconds: float = 0.0,
        minutes: float = 0.0,
        hours: float = 0.0,
        delta: Optional[datetime.timedelta] = None,
        time_of_day: Optional[datetime.time] = None,
        on_error: Optional[Callable[[Exception], Awaitable[None]]] = None,
        before_loop: Optional[Callable[[], Awaitable[None] | None]] = None,
        after_loop: Optional[Callable[[], Awaitable[None] | None]] = None,
    ) -> None:
        self._coro = coro
        self._task: Optional[asyncio.Task[None]] = None
        if time_of_day is not None and (
            seconds or minutes or hours or delta is not None
        ):
            raise ValueError("time_of_day cannot be used with an interval")

        if delta is not None:
            if not isinstance(delta, datetime.timedelta):
                raise TypeError("delta must be a datetime.timedelta")
            interval_seconds = delta.total_seconds()
        else:
            interval_seconds = seconds + minutes * 60.0 + hours * 3600.0

        self._seconds = float(interval_seconds)
        self._time_of_day = time_of_day
        self._on_error = on_error
        self._before_loop = before_loop
        self._after_loop = after_loop

    def _seconds_until_time(self) -> float:
        assert self._time_of_day is not None
        now = datetime.datetime.now()
        target = datetime.datetime.combine(now.date(), self._time_of_day)
        if target <= now:
            target += datetime.timedelta(days=1)
        return (target - now).total_seconds()

    async def _run(self, *args: Any, **kwargs: Any) -> None:
        try:
            if self._before_loop is not None:
                await _maybe_call_no_args(self._before_loop)

            first = True
            while True:
                if self._time_of_day is not None:
                    await asyncio.sleep(self._seconds_until_time())
                elif not first:
                    await asyncio.sleep(self._seconds)

                try:
                    await self._coro(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    if self._on_error is not None:
                        await _maybe_call(self._on_error, exc)
                    else:
                        raise

                first = False
        except asyncio.CancelledError:
            pass
        finally:
            if self._after_loop is not None:
                await _maybe_call_no_args(self._after_loop)

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


async def _maybe_call(
    func: Callable[[Exception], Awaitable[None] | None], exc: Exception
) -> None:
    result = func(exc)
    if asyncio.iscoroutine(result):
        await result


async def _maybe_call_no_args(func: Callable[[], Awaitable[None] | None]) -> None:
    result = func()
    if asyncio.iscoroutine(result):
        await result


class _Loop:
    def __init__(
        self,
        func: Callable[..., Awaitable[Any]],
        *,
        seconds: float = 0.0,
        minutes: float = 0.0,
        hours: float = 0.0,
        delta: Optional[datetime.timedelta] = None,
        time_of_day: Optional[datetime.time] = None,
        on_error: Optional[Callable[[Exception], Awaitable[None]]] = None,
    ) -> None:
        self.func = func
        self.seconds = seconds
        self.minutes = minutes
        self.hours = hours
        self.delta = delta
        self.time_of_day = time_of_day
        self.on_error = on_error
        self._task: Optional[Task] = None
        self._owner: Any = None
        self._before_loop: Optional[Callable[..., Awaitable[Any]]] = None
        self._after_loop: Optional[Callable[..., Awaitable[Any]]] = None

    def __get__(self, obj: Any, objtype: Any) -> "_BoundLoop":
        return _BoundLoop(self, obj)

    def _coro(self, *args: Any, **kwargs: Any) -> Awaitable[Any]:
        if self._owner is None:
            return self.func(*args, **kwargs)
        return self.func(self._owner, *args, **kwargs)

    def before_loop(
        self, func: Callable[..., Awaitable[Any]]
    ) -> Callable[..., Awaitable[Any]]:
        self._before_loop = func
        return func

    def after_loop(
        self, func: Callable[..., Awaitable[Any]]
    ) -> Callable[..., Awaitable[Any]]:
        self._after_loop = func
        return func

    def start(self, *args: Any, **kwargs: Any) -> asyncio.Task[None]:
        def call_before() -> Awaitable[None] | None:
            if self._before_loop is None:
                return None
            if self._owner is not None:
                return self._before_loop(self._owner)
            return self._before_loop()

        def call_after() -> Awaitable[None] | None:
            if self._after_loop is None:
                return None
            if self._owner is not None:
                return self._after_loop(self._owner)
            return self._after_loop()

        self._task = Task(
            self._coro,
            seconds=self.seconds,
            minutes=self.minutes,
            hours=self.hours,
            delta=self.delta,
            time_of_day=self.time_of_day,
            on_error=self.on_error,
            before_loop=call_before,
            after_loop=call_after,
        )
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


def loop(
    *,
    seconds: float = 0.0,
    minutes: float = 0.0,
    hours: float = 0.0,
    delta: Optional[datetime.timedelta] = None,
    time_of_day: Optional[datetime.time] = None,
    on_error: Optional[Callable[[Exception], Awaitable[None]]] = None,
) -> Callable[[Callable[..., Awaitable[Any]]], _Loop]:
    """Decorator to create a looping task."""

    def decorator(func: Callable[..., Awaitable[Any]]) -> _Loop:
        return _Loop(
            func,
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            delta=delta,
            time_of_day=time_of_day,
            on_error=on_error,
        )

    return decorator
