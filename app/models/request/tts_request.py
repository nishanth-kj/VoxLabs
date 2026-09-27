from pydantic import BaseModel


class TTSRequest(BaseModel):
    """Speech generation settings. `text` is checked by the service (required, max length).

    `engine_voice` picks one of the engine's built-in voices (e.g. Kokoro "af_bella", an Edge short
    name) without creating a voice first; it overrides the voice's own `engine_voice`. With `cache`,
    a request identical to an earlier one returns that audio instead of generating it again.
    """

    text: str
    voices_id: int | None = None
    model_key: str | None = None
    engine_voice: str | None = None
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
    name: str | None = None
    background: bool = False
    cache: bool = False
