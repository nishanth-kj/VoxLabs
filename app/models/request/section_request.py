from pydantic import BaseModel


class SectionRequest(BaseModel):
    script_sections_id: int
    voices_id: int | None = None
    speed: float | None = None
    pitch: float | None = None
    emotion: str | None = None
    style: str | None = None
    pause_after_ms: int | None = None
    text: str | None = None
    speaker: str | None = None
