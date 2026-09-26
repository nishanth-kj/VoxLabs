from pydantic import BaseModel


class VoiceRequest(BaseModel):
    """Create a preset voice (no `voices_id`), update (`voices_id`) or delete (`voices_id` + status Deleted).

    Cloned voices are created with the multipart `POST /api/voices/clone` form instead.
    """

    voices_id: int | None = None
    status: int | None = None
    name: str | None = None
    description: str | None = None
    language: str | None = None
    model_key: str | None = None
    engine_voice: str | None = None
    users_id: int | None = None
