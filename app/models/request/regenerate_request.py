from pydantic import BaseModel


class RegenerateRequest(BaseModel):
    audios_id: int
    seed: int | None = None
