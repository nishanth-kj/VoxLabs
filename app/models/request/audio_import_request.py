from fastapi import UploadFile
from pydantic import BaseModel


class AudioImportRequest(BaseModel):
    """Multipart form for POST /api/audio/import."""

    file: UploadFile
    projects_id: int | None = None
