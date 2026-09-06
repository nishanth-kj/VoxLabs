from enum import Enum


class ModelKind(str, Enum):
    ENGINE = "engine"
    VOICE = "voice"


class ModelProvider(str, Enum):
    LOCAL = "local"
    MICROSOFT = "microsoft"
