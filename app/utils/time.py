"""Timezone-aware time helpers. All stored timestamps are UTC."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    """SQLite drops tzinfo; re-attach UTC to naive values read back from it."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def iso(value: datetime | None) -> str | None:
    value = as_utc(value)
    return value.isoformat(timespec="seconds") if value else None


def local_display(value: datetime | None) -> str:
    value = as_utc(value)
    return value.astimezone().strftime("%Y-%m-%d %H:%M") if value else ""


def format_duration(seconds: float | None) -> str:
    if not seconds:
        return "0:00.0"
    minutes, secs = divmod(float(seconds), 60)
    return f"{int(minutes)}:{secs:04.1f}"
