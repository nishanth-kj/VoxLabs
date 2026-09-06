from enum import Enum


class BaseEnum(Enum):
    def __init__(self, code: int, value: str):
        self.code = code
        self.value = value

