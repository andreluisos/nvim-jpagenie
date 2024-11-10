from enum import Enum


class Other(Enum):
    MANDATORY = "mandatory"
    UNIQUE = "unique"
    ORPHAN_REMOVAL = "orphan_removal"
    LARGE_OBJECT = "large_object"
    EQUALS_HASHCODE = "equals_hashcode"
    MUTABLE = "mutable"

    @classmethod
    def from_value(cls, value: str) -> "Other":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
