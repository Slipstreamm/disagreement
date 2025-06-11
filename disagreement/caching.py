from __future__ import annotations

import operator
from typing import Any, Callable, ClassVar, Dict, Iterator, Tuple


class _MemberCacheFlagValue:
    flag: int

    def __init__(self, func: Callable[[Any], bool]):
        self.flag = getattr(func, "flag", 0)
        self.__doc__ = func.__doc__

    def __get__(self, instance: "MemberCacheFlags", owner: type) -> Any:
        if instance is None:
            return self
        return instance.value & self.flag != 0

    def __set__(self, instance: Any, value: bool) -> None:
        if value:
            instance.value |= self.flag
        else:
            instance.value &= ~self.flag

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} flag={self.flag}>"


def flag_value(flag: int) -> Callable[[Callable[[Any], bool]], _MemberCacheFlagValue]:
    def decorator(func: Callable[[Any], bool]) -> _MemberCacheFlagValue:
        setattr(func, "flag", flag)
        return _MemberCacheFlagValue(func)

    return decorator


class MemberCacheFlags:
    __slots__ = ("value",)

    VALID_FLAGS: ClassVar[Dict[str, int]] = {
        "joined": 1 << 0,
        "voice": 1 << 1,
        "online": 1 << 2,
    }
    DEFAULT_FLAGS: ClassVar[int] = 1 | 2 | 4
    ALL_FLAGS: ClassVar[int] = sum(VALID_FLAGS.values())

    def __init__(self, **kwargs: bool):
        self.value = self.DEFAULT_FLAGS
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f"{key!r} is not a valid member cache flag.")
            setattr(self, key, value)

    @classmethod
    def _from_value(cls, value: int) -> MemberCacheFlags:
        self = cls.__new__(cls)
        self.value = value
        return self

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MemberCacheFlags) and self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"<MemberCacheFlags value={self.value}>"

    def __iter__(self) -> Iterator[Tuple[str, bool]]:
        for name in self.VALID_FLAGS:
            yield name, getattr(self, name)

    def __int__(self) -> int:
        return self.value

    def __index__(self) -> int:
        return self.value

    @classmethod
    def all(cls) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` with all flags enabled."""
        return cls._from_value(cls.ALL_FLAGS)

    @classmethod
    def none(cls) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` with all flags disabled."""
        return cls._from_value(0)

    @classmethod
    def only_joined(cls) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` with only the `joined` flag enabled."""
        return cls._from_value(cls.VALID_FLAGS["joined"])

    @classmethod
    def only_voice(cls) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` with only the `voice` flag enabled."""
        return cls._from_value(cls.VALID_FLAGS["voice"])

    @classmethod
    def only_online(cls) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` with only the `online` flag enabled."""
        return cls._from_value(cls.VALID_FLAGS["online"])

    @flag_value(1 << 0)
    def joined(self) -> bool:
        """Whether to cache members that have just joined the guild."""
        return False

    @flag_value(1 << 1)
    def voice(self) -> bool:
        """Whether to cache members that are in a voice channel."""
        return False

    @flag_value(1 << 2)
    def online(self) -> bool:
        """Whether to cache members that are online."""
        return False
