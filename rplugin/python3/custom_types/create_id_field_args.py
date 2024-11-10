from dataclasses import dataclass, field, InitVar
from typing import List, Optional
from custom_types.id_generation import IdGeneration
from custom_types.id_generation_type import IdGenerationType
from custom_types.other import Other


@dataclass
class CreateIdEntityFieldArgs:
    field_package_path: str
    field_type: str
    field_name: str
    id_generation: InitVar[str]
    id_generation_enum: IdGeneration = field(init=False)
    id_generation_type: InitVar[str]
    id_generation_type_enum: IdGenerationType = field(init=False)
    generator_name: Optional[str] = None
    sequence_name: Optional[str] = None
    initial_value: Optional[int] = None
    allocation_size: Optional[int] = None
    other: InitVar[Optional[List[str]]] = None
    other_enum: List[Other] = field(init=False, default_factory=list)

    def __post_init__(
        self, id_generation: str, id_generation_type: str, other: Optional[List[str]]
    ):
        self.id_generation_enum = IdGeneration.from_value(id_generation)
        self.id_generation_type_enum = IdGenerationType.from_value(id_generation_type)
        other = other or []
        self.other_enum = [Other.from_value(value) for value in other]
        self.initial_value = (
            int(self.initial_value) if self.initial_value is not None else None
        )
        self.allocation_size = (
            int(self.allocation_size) if self.allocation_size is not None else None
        )

