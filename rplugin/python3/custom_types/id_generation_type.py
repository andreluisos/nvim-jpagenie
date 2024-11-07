from enum import Enum


class IdGenerationType(Enum):
    NONE = "none"
    ORM_PROVIDED = "orm_provided"
    ENTITY_EXCLUSIVE_GENERATION = "entity_exclusive_generation"

    @classmethod
    def from_value(cls, value: str) -> "IdGenerationType":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
