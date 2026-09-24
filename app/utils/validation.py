"""Validation utils.

`Validation` checks input values (raising ValidationError with a user-facing
message and the offending field) and converts output data to JSON-correct
types before it is sent in an ApiResponse.

    projects_id = Validation.optional_id(projects_id, "projects_id")
    limit = Validation.limit(limit)
    data = audio_service.list_audios(projects_id, limit)
    return ApiResponse(data).success()
"""

import math
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel

from app.constants.audio import EMOTIONS, IMPORT_FORMATS
from app.exceptions import ValidationError
from app.utils.logger import logger

MAX_TEXT_LENGTH = 200_000
MAX_LIMIT = 1000


class Validation:
    # ------------------------------------------------------------ inputs

    @staticmethod
    def require_text(text: str | None, field: str = "text", max_length: int = MAX_TEXT_LENGTH) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValidationError("Text is required", field=field)
        if len(cleaned) > max_length:
            raise ValidationError(f"Text is too long ({len(cleaned)} > {max_length} characters)", field=field)
        return cleaned

    @staticmethod
    def require_name(name: str | None, field: str = "name", max_length: int = 120) -> str:
        cleaned = (name or "").strip()
        if not cleaned:
            raise ValidationError("Name is required", field=field)
        if len(cleaned) > max_length:
            raise ValidationError(f"Name must be at most {max_length} characters", field=field)
        return cleaned

    @staticmethod
    def require_id(value: int | str | None, field: str) -> int:
        """A database id: a positive integer."""
        if value is None or isinstance(value, bool):
            raise ValidationError(f"{field} is required", field=field)
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ValidationError(f"{field} must be a number", field=field) from None
        if number < 1:
            raise ValidationError(f"{field} must be a positive number", field=field)
        return number

    @staticmethod
    def optional_id(value: int | str | None, field: str) -> int | None:
        return None if value is None else Validation.require_id(value, field)

    @staticmethod
    def require_ref(value: int | str | None, field: str) -> str | int:
        """A numeric id or a key (models accept either)."""
        if isinstance(value, int) and not isinstance(value, bool):
            return Validation.require_id(value, field)
        cleaned = str(value or "").strip()
        if not cleaned:
            raise ValidationError(f"{field} is required", field=field)
        return int(cleaned) if cleaned.isdigit() else cleaned

    @staticmethod
    def limit(value: int | None, field: str = "limit", default: int = 100, maximum: int = MAX_LIMIT) -> int:
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
            raise ValidationError(f"{field} must be between 1 and {maximum}", field=field)
        return value

    @staticmethod
    def require_audio_file(path: str | Path | None, field: str = "audio") -> Path:
        if not path:
            raise ValidationError("An audio file is required", field=field)
        path = Path(path)
        if not path.is_file():
            raise ValidationError(f"File not found: {path.name}", field=field)
        if path.suffix.lower().lstrip(".") not in IMPORT_FORMATS:
            raise ValidationError(
                f"Unsupported format '{path.suffix}'. Use one of: {', '.join(IMPORT_FORMATS)}", field=field
            )
        if path.stat().st_size == 0:
            raise ValidationError(f"{path.name} is empty", field=field)
        return path

    @staticmethod
    def in_range(value: float | None, low: float, high: float, field: str, default: float) -> float:
        if value is None:
            return default
        value = float(value)
        if not low <= value <= high:
            raise ValidationError(f"{field} must be between {low} and {high}", field=field)
        return value

    @staticmethod
    def require_emotion(emotion: str | None) -> str:
        emotion = (emotion or "neutral").lower()
        if emotion not in EMOTIONS:
            raise ValidationError(f"Unknown emotion '{emotion}'", field="emotion")
        return emotion

    @staticmethod
    def require_choice(value: str, choices, field: str) -> str:
        if value not in choices:
            raise ValidationError(f"{field} must be one of: {', '.join(map(str, choices))}", field=field)
        return value

    # ------------------------------------------------------------ output

    @staticmethod
    def response_data(data: Any) -> Any:
        """Convert service results to JSON-correct types (ints, floats, strings, lists, dicts, null)."""
        if data is None or isinstance(data, (bool, int, str)):
            return data
        if isinstance(data, float):
            return data if math.isfinite(data) else None
        if isinstance(data, Enum):
            return data._value_  # BaseEnum members store their integer code here
        if isinstance(data, (datetime, date)):
            return data.isoformat()
        if isinstance(data, Path):
            return str(data)
        if isinstance(data, np.generic):
            return Validation.response_data(data.item())
        if isinstance(data, np.ndarray):
            return Validation.response_data(data.tolist())
        if isinstance(data, BaseModel):
            return Validation.response_data(data.model_dump())
        if isinstance(data, dict):
            return {str(key): Validation.response_data(value) for key, value in data.items()}
        if isinstance(data, (list, tuple, set, frozenset)):
            return [Validation.response_data(value) for value in data]
        logger.warning(f"Unexpected {type(data).__name__} in response data; sent as text")
        return str(data)
