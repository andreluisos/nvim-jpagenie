from enum import Enum


class FieldTimeZoneStorage(Enum):
    NATIVE = "NATIVE"
    NORMALIZE = "NORMALIZE"
    NORMALIZE_UTC = "NORMALIZE_UTC"
    COLUMN = "COLUMN"
    AUTO = "AUTO"

    @classmethod
    def from_value(cls, value: str) -> "FieldTimeZoneStorage":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
