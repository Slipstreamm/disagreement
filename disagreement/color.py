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

    # Discord brand colors
    @classmethod
    def blurple(cls) -> "Color":
        """Discord brand blurple (#5865F2)."""
        return cls(0x5865F2)

    @classmethod
    def light_blurple(cls) -> "Color":
        """Light blurple used by Discord (#E0E3FF)."""
        return cls(0xE0E3FF)

    @classmethod
    def legacy_blurple(cls) -> "Color":
        """Legacy Discord blurple (#7289DA)."""
        return cls(0x7289DA)

    # Additional assorted colors
    @classmethod
    def teal(cls) -> "Color":
        return cls(0x1ABC9C)

    @classmethod
    def dark_teal(cls) -> "Color":
        return cls(0x11806A)

    @classmethod
    def brand_green(cls) -> "Color":
        return cls(0x57F287)

    @classmethod
    def dark_green(cls) -> "Color":
        return cls(0x206694)

    @classmethod
    def orange(cls) -> "Color":
        return cls(0xE67E22)

    @classmethod
    def dark_orange(cls) -> "Color":
        return cls(0xA84300)

    @classmethod
    def brand_red(cls) -> "Color":
        return cls(0xED4245)

    @classmethod
    def dark_red(cls) -> "Color":
        return cls(0x992D22)

    @classmethod
    def magenta(cls) -> "Color":
        return cls(0xE91E63)

    @classmethod
    def dark_magenta(cls) -> "Color":
        return cls(0xAD1457)

    @classmethod
    def purple(cls) -> "Color":
        return cls(0x9B59B6)

    @classmethod
    def dark_purple(cls) -> "Color":
        return cls(0x71368A)

    @classmethod
    def yellow(cls) -> "Color":
        return cls(0xF1C40F)

    @classmethod
    def dark_gold(cls) -> "Color":
        return cls(0xC27C0E)

    @classmethod
    def light_gray(cls) -> "Color":
        return cls(0x99AAB5)

    @classmethod
    def dark_gray(cls) -> "Color":
        return cls(0x2C2F33)

    @classmethod
    def lighter_gray(cls) -> "Color":
        return cls(0xBFBFBF)

    @classmethod
    def darker_gray(cls) -> "Color":
        return cls(0x23272A)

    @classmethod
    def black(cls) -> "Color":
        return cls(0x000000)

    @classmethod
    def white(cls) -> "Color":
        return cls(0xFFFFFF)

    def to_rgb(self) -> tuple[int, int, int]:
        return ((self.value >> 16) & 0xFF, (self.value >> 8) & 0xFF, self.value & 0xFF)

    @classmethod
    def parse(
        cls, value: "Color | int | str | tuple[int, int, int] | None"
    ) -> "Color | None":
        """Convert ``value`` to a :class:`Color` instance.

        Parameters
        ----------
        value:
            The value to convert. May be ``None``, an existing ``Color``, an
            integer in the ``0xRRGGBB`` format, or a hex string like ``"#RRGGBB"``.

        Returns
        -------
        Optional[Color]
            A ``Color`` object if ``value`` is not ``None``.
        """

        if value is None:
            return None
        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return cls(value)
        if isinstance(value, str):
            return cls.from_hex(value)
        if isinstance(value, tuple) and len(value) == 3:
            return cls.from_rgb(*value)
        raise TypeError("Color value must be Color, int, str, tuple, or None")
