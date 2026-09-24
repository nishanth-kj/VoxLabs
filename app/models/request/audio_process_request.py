from pydantic import BaseModel


class AudioProcessRequest(BaseModel):
    """Enhance with `steps`/`preset`, or render a non-destructive edit list with `ops`."""

    audios_id: int
    steps: dict | None = None
    preset: str | None = None
    ops: list[dict] | None = None
    background: bool = False
