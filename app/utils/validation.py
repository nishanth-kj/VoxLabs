"""Input validation helpers. Each raises ValidationError with a user-facing message."""

from pathlib import Path

from app.constants.audio import EMOTIONS, IMPORT_FORMATS
from app.exceptions import ValidationError

MAX_TEXT_LENGTH = 200_000


def require_text(text: str | None, field: str = "text", max_length: int = MAX_TEXT_LENGTH) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValidationError("Text is required", field=field)
    if len(cleaned) > max_length:
        raise ValidationError(f"Text is too long ({len(cleaned)} > {max_length} characters)", field=field)
    return cleaned


def require_name(name: str | None, field: str = "name", max_length: int = 120) -> str:
    cleaned = (name or "").strip()
    if not cleaned:
        raise ValidationError("Name is required", field=field)
    if len(cleaned) > max_length:
        raise ValidationError(f"Name must be at most {max_length} characters", field=field)
    return cleaned


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


def in_range(value: float | None, low: float, high: float, field: str, default: float) -> float:
    if value is None:
        return default
    value = float(value)
    if not low <= value <= high:
        raise ValidationError(f"{field} must be between {low} and {high}", field=field)
    return value


def require_emotion(emotion: str | None) -> str:
    emotion = (emotion or "neutral").lower()
    if emotion not in EMOTIONS:
        raise ValidationError(f"Unknown emotion '{emotion}'", field="emotion")
    return emotion


def require_choice(value: str, choices, field: str) -> str:
    if value not in choices:
        raise ValidationError(f"{field} must be one of: {', '.join(map(str, choices))}", field=field)
    return value
