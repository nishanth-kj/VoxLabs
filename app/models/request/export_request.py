from pydantic import BaseModel


class ExportRequest(BaseModel):
    """Save an export: no id exports `audios_id` in `format` (like POST /api/audio/export) and records it;
    an id with `status` Deleted removes it from the list, and the file as well with `delete_file`."""

    exports_id: int | None = None
    audios_id: int | None = None
    format: str = "wav"
    sample_rate: int | None = None
    status: int | None = None
    delete_file: bool = False
