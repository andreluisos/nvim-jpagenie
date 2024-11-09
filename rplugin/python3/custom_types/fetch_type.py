from enum import Enum


class FetchType(Enum):
    LAZY = "lazy"
    EAGER = "eager"
    NONE = "none"

    @classmethod
    def from_value(cls, value: str) -> "FetchType":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
