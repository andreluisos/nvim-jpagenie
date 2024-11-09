from enum import Enum


class CollectionType(Enum):
    SET = "set"
    LIST = "list"
    COLLECTION = "collection"

    @classmethod
    def from_value(cls, value: str) -> "CollectionType":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
