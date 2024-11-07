from enum import Enum


class IdGeneration(Enum):
    NONE = "none"
    AUTO = "auto"
    IDENTITY = "identity"
    SEQUENCE = "sequence"

    @classmethod
    def from_value(cls, value: str) -> "IdGeneration":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
