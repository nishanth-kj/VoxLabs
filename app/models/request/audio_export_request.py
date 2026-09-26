from pydantic import BaseModel


class AudioExportRequest(BaseModel):
    audios_id: int
    format: str = "wav"
    sample_rate: int | None = None
