from pydantic import BaseModel


class ProjectRequest(BaseModel):
    """Create (no `projects_id`), update (`projects_id`) or delete (`projects_id` + status Deleted)."""

    projects_id: int | None = None
    status: int | None = None
    name: str | None = None
    project_type: str | None = None
    description: str | None = None
    users_id: int | None = None
    edit_state: dict | None = None
    settings: dict | None = None
