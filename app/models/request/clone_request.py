from fastapi import UploadFile
from pydantic import BaseModel


class CloneRequest(BaseModel):
    """Multipart form for POST /api/voices/clone. Consent fields are required."""

    name: str
    consent: bool
    granted_by: str
    speaker_name: str
    statement: str = ""
    language: str = "en"
    description: str = ""
    model_key: str | None = None
    users_id: int | None = None
    background: bool = False
    samples: list[UploadFile]
