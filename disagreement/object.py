class Object:
    """A minimal wrapper around a Discord snowflake ID."""

    __slots__ = ("id",)

    def __init__(self, object_id: int) -> None:
        self.id = int(object_id)

    def __int__(self) -> int:
        return self.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Object) and self.id == other.id

    def __repr__(self) -> str:
        return f"<Object id={self.id}>"
