from pydantic import BaseModel


class ScriptRequest(BaseModel):
    """Create (no `scripts_id`), update (`scripts_id`) or delete (`scripts_id` + status Deleted)."""

    scripts_id: int | None = None
    status: int | None = None
    title: str | None = None
    body: str | None = None
    projects_id: int | None = None
    speaker_map: dict[str, int | None] | None = None
    settings: dict | None = None
