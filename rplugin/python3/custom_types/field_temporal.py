from enum import Enum


class FieldTemporal(Enum):
    DATE = "DATE"
    TIME = "TIME"
    TIMESTAMP = "TIMESTAMP"

    @classmethod
    def from_value(cls, value: str) -> "FieldTemporal":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
