"""Simple color helper similar to discord.py's Color class."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Color:
    """Represents an RGB color value."""

    value: int

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 0xFFFFFF:
            raise ValueError("Color value must be between 0x000000 and 0xFFFFFF")

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> "Color":
        """Create a Color from red, green and blue components."""
        if not all(0 <= c <= 255 for c in (r, g, b)):
            raise ValueError("RGB components must be between 0 and 255")
        return cls((r << 16) + (g << 8) + b)

    @classmethod
    def from_hex(cls, value: str) -> "Color":
        """Create a Color from a hex string like ``"#ff0000"``."""
        value = value.lstrip("#")
        if len(value) != 6:
            raise ValueError("Hex string must be in RRGGBB format")
        return cls(int(value, 16))

    @classmethod
    def default(cls) -> "Color":
        return cls(0)

    @classmethod
    def red(cls) -> "Color":
        return cls(0xFF0000)

    @classmethod
    def green(cls) -> "Color":
        return cls(0x00FF00)

    @classmethod
    def blue(cls) -> "Color":
        return cls(0x0000FF)

    def to_rgb(self) -> tuple[int, int, int]:
        return ((self.value >> 16) & 0xFF, (self.value >> 8) & 0xFF, self.value & 0xFF)
