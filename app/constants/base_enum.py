"""Abstract base for integer-coded constants.

Members are declared as `(code, value)`: `code` is the INTEGER stored in the
database, `value` is the readable PascalCase label.

    class Status(BaseEnum):
        IN_PROGRESS = (4, "InProgress")

    Status.IN_PROGRESS.code   # 4
    Status.IN_PROGRESS.value  # "InProgress"
    Status(4)                 # Status.IN_PROGRESS (lookup by code)
"""

from enum import Enum


class BaseEnum(Enum):
    _label: str

    def __new__(cls, code: int, value: str):
        member = object.__new__(cls)
        member._value_ = code
        member._label = value
        return member

    @property
    def code(self) -> int:
        return self._value_

    @property
    def value(self) -> str:  # type: ignore[override]
        return self._label

    @classmethod
    def from_code(cls, code: int) -> "BaseEnum":
        return cls(int(code))

    @classmethod
    def label(cls, code: int) -> str:
        try:
            return cls(int(code)).value
        except ValueError:
            return str(code)

    @classmethod
    def choices(cls) -> list[tuple[int, str]]:
        return [(member.code, member.value) for member in cls]
