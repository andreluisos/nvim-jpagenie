from dataclasses import dataclass, field, InitVar
from typing import Optional
from custom_types.entity_type import EntityType


@dataclass
class CreateEntityArgs:
    package_path: str
    entity_name: str
    entity_type: InitVar[str]
    entity_type_enum: EntityType = field(init=False)
    parent_entity_type: Optional[str] = None
    parent_entity_package_path: Optional[str] = None

    def __post_init__(self, entity_type: str):
        self.entity_type_enum = EntityType.from_value(entity_type)
