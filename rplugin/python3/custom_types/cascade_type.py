from enum import Enum


class CascadeType(Enum):
    ALL = "all"
    PERSIST = "persist"
    MERGE = "merge"
    REMOVE = "remove"
    REFRESH = "refresh"
    DETACH = "detach"
