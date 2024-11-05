from enum import Enum


class FieldTimeZoneStorage(Enum):
    NATIVE = "NATIVE"
    NORMALIZE = "NORMALIZE"
    NORMALIZE_UTC = "NORMALIZE_UTC"
    COLUMN = "COLUMN"
    AUTO = "AUTO"
