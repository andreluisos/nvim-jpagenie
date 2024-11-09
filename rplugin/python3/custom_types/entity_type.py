from enum import Enum


class EntityType(Enum):
    ENTITY = "entity"
    EMBEDDABLE = "embeddable"
    MAPPED_SUPERCLASS = "mapped_superclass"

    @classmethod
    def from_value(cls, value: str) -> "EntityType":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
