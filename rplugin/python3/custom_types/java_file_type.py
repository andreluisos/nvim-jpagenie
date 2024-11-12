from enum import Enum


class JavaFileType(Enum):
    CLASS = "class"
    INTERFACE = "interface"
    RECORD = "record"
    ENUM = "enum"
    ANNOTATION = "annotation"

    @classmethod
    def from_value(cls, value: str) -> "JavaFileType":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value '{value}'")
