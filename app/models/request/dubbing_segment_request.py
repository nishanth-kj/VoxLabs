from pydantic import BaseModel


class DubbingSegmentRequest(BaseModel):
    """Create, update or delete a dubbing timeline segment."""

    dubbing_segments_id: int | None = None
    dubbing_projects_id: int | None = None
    status: int | None = None
    position: int | None = None
    start_ms: int | None = None
    end_ms: int | None = None
    speaker: str | None = None
    source_text: str | None = None
    target_text: str | None = None
    voices_id: int | None = None
    speed: float | None = None
    pitch: float | None = None
    emotion: str | None = None
    locked: bool | None = None

