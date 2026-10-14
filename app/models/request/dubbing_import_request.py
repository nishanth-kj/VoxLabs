from pydantic import BaseModel


class DubbingImportRequest(BaseModel):
    """Import SRT or WebVTT subtitles into a dubbing project."""

    dubbing_projects_id: int
    content: str
    format: str = "srt"  # "srt" | "vtt"
    replace_existing: bool = True

