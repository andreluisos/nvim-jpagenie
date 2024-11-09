from enum import Enum


class CascadeType(Enum):
    ALL = "all"
    PERSIST = "persist"
    MERGE = "merge"
    REMOVE = "remove"
    REFRESH = "refresh"
    DETACH = "detach"

    @classmethod
    def from_value(cls, value: str) -> "CascadeType":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
