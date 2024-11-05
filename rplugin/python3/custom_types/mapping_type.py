from enum import Enum


class MappingType(Enum):
    UNIDIRECTIONAL_JOIN_COLUMN = "unidirectional_join_column"
    BIDIRECTIONAL_JOIN_COLUMN = "bidirectional_join_column"
