from dataclasses import dataclass, field, InitVar
from typing import List, Optional
from custom_types.fetch_type import FetchType
from custom_types.collection_type import CollectionType
from custom_types.mapping_type import MappingType
from custom_types.cascade_type import CascadeType
from custom_types.other import Other


@dataclass
class CreateManyToOneRelArgs:
    inverse_field_type: str
    fetch_type: InitVar[str]
    fetch_type_enum: FetchType = field(init=False)
    collection_type: InitVar[str]
    collection_type_enum: CollectionType = field(init=False)
    mapping_type: InitVar[Optional[str]] = None
    mapping_type_enum: Optional[MappingType] = field(init=False)
    owning_side_cascades: InitVar[Optional[List[str]]] = None
    owning_side_cascades_enum: List[CascadeType] = field(
        init=False, default_factory=list
    )
    inverse_side_cascades: InitVar[Optional[List[str]]] = None
    inverse_side_cascades_enum: List[CascadeType] = field(
        init=False, default_factory=list
    )
    owning_side_other: InitVar[Optional[List[str]]] = None
    owning_side_other_enum: List[Other] = field(init=False, default_factory=list)
    inverse_side_other: InitVar[Optional[List[str]]] = None
    inverse_side_other_enum: List[Other] = field(init=False, default_factory=list)

    def __post_init__(
        self,
        fetch_type: str,
        collection_type: str,
        mapping_type: Optional[str],
        owning_side_cascades: Optional[List[str]],
        inverse_side_cascades: Optional[List[str]],
        owning_side_other: Optional[List[str]],
        inverse_side_other: Optional[List[str]],
    ):
        self.fetch_type_enum = FetchType.from_value(fetch_type)
        self.collection_type_enum = CollectionType.from_value(collection_type)
        self.mapping_type_enum = (
            MappingType.from_value(mapping_type) if mapping_type else None
        )
        owning_side_cascades = owning_side_cascades or []
        self.owning_side_cascades_enum = [
            CascadeType.from_value(value) for value in owning_side_cascades
        ]
        inverse_side_cascades = inverse_side_cascades or []
        self.inverse_side_cascades_enum = [
            CascadeType.from_value(value) for value in inverse_side_cascades
        ]
        owning_side_other = owning_side_other or []
        self.owning_side_other_enum = [
            Other.from_value(value) for value in owning_side_other
        ]
        inverse_side_other = inverse_side_other or []
        self.inverse_side_other_enum = [
            Other.from_value(value) for value in inverse_side_other
        ]
