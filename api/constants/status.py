from .baseEnum import BaseEnum


class Status(BaseEnum):
    ACTIVE = (1, "Active")
    INACTIVE = (2, "Inactive")
    PENDING = (3, "Pending")