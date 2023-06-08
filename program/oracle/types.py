from enum import IntEnum


class ModelStatus(IntEnum):
    ACTIVE = 1
    INACTIVE = 2
    FROZEN = 3
    OBSOLETE = 4
