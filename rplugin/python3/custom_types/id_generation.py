from enum import Enum


class IdGeneration(Enum):
    NONE = "none"
    AUTO = "auto"
    IDENTITY = "identity"
    SEQUENCE = "sequence"
