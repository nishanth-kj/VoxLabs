from pydantic import BaseModel


class TTSRequest(BaseModel):
    """Speech generation settings. `text` is checked by the service (required, max length)."""

    text: str
    voices_id: int | None = None
    model_key: str | None = None
    speed: float = 1.0
    pitch: float = 1.0
    energy: float = 1.0
    emotion: str = "neutral"
    style: str = "default"
    pause_ms: int | None = None
    pronunciations: dict[str, str] | None = None
    temperature: float | None = None
    seed: int | None = None
    post: dict | None = None
    preset: str | None = None
    projects_id: int | None = None
    name: str | None = None
    background: bool = False
