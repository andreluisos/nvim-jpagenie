from enum import Enum


class MappingType(Enum):
    UNIDIRECTIONAL_JOIN_COLUMN = "unidirectional_join_column"
    BIDIRECTIONAL_JOIN_COLUMN = "bidirectional_join_column"

    @classmethod
    def from_value(cls, value: str) -> "MappingType":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
