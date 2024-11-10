from dataclasses import dataclass, field, InitVar
from typing import List, Optional
from custom_types.field_time_zone_storage import FieldTimeZoneStorage
from custom_types.field_temporal import FieldTemporal
from custom_types.other import Other


@dataclass
class CreateBasicEntityFieldArgs:
    field_package_path: str
    field_type: str
    field_name: str
    field_length: Optional[int] = None
    field_precision: Optional[int] = None
    field_scale: Optional[int] = None
    field_time_zone_storage: InitVar[Optional[str]] = None
    field_time_zone_storage_enum: Optional[FieldTimeZoneStorage] = field(init=False)
    field_temporal: InitVar[Optional[str]] = None
    field_temporal_enum: Optional[FieldTemporal] = field(init=False)
    other: InitVar[Optional[List[str]]] = None
    other_enum: List[Other] = field(init=False, default_factory=list)

    def __post_init__(
        self,
        field_time_zone_storage: Optional[str],
        field_temporal: Optional[str],
        other: Optional[List[str]],
    ):
        self.field_time_zone_storage_enum = (
            FieldTimeZoneStorage.from_value(field_time_zone_storage)
            if field_time_zone_storage
            else None
        )
        self.field_temporal_enum = (
            FieldTemporal.from_value(field_temporal) if field_temporal else None
        )
        other = other or []
        self.other_enum = [Other.from_value(value) for value in other]
        self.field_length = (
            int(self.field_length) if self.field_length is not None else None
        )
        self.field_precision = (
            int(self.field_precision) if self.field_precision is not None else None
        )
        self.field_scale = (
            int(self.field_scale) if self.field_scale is not None else None
        )
