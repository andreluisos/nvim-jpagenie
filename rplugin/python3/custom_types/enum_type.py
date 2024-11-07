from enum import Enum


class EnumType(Enum):
    ORDINAL = "ORDINAL"
    STRING = "STRING"

    @classmethod
    def from_value(cls, value: str) -> "EnumType":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
