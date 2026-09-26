from pydantic import BaseModel


class UserRequest(BaseModel):
    """Create (no `users_id`), update (`users_id`) or delete (`users_id` + status Deleted)."""

    users_id: int | None = None
    status: int | None = None
    name: str | None = None
    email: str | None = None
