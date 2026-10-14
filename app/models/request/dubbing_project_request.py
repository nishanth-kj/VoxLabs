from pydantic import BaseModel


class DubbingProjectRequest(BaseModel):
    """Create (no `dubbing_projects_id`), update (`dubbing_projects_id`) or delete (`dubbing_projects_id` + status Deleted)."""

    dubbing_projects_id: int | None = None
    status: int | None = None
    title: str | None = None
    source_media_path: str | None = None
    source_language: str | None = None
    target_language: str | None = None
    speaker_map: dict[str, int | None] | None = None
    settings: dict | None = None

