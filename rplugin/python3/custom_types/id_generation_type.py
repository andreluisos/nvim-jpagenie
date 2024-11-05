from enum import Enum


class IdGenerationType(Enum):
    NONE = "none"
    ORM_PROVIDED = "orm_provided"
    ENTITY_EXCLUSIVE_GENERATION = "entity_exclusive_generation"
