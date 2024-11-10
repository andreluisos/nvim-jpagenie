from dataclasses import dataclass, field, InitVar
from typing import List, Optional
from custom_types.enum_type import EnumType
from custom_types.other import Other


@dataclass
class CreateEnumEntityFieldArgs:
    field_path: str
    field_package_path: str
    field_type: str
    field_name: str
    enum_type: InitVar[str]
    enum_type_enum: EnumType = field(init=False)
    field_length: Optional[int] = None
    other: InitVar[Optional[List[str]]] = None
    other_enum: List[Other] = field(init=False, default_factory=list)

    def __post_init__(self, enum_type: str, other: Optional[List[str]]):
        self.enum_type_enum = EnumType.from_value(enum_type)
        self.field_length = (
            int(self.field_length) if self.field_length is not None else None
        )
        other = other or []
        self.other_enum = [Other.from_value(value) for value in other]
