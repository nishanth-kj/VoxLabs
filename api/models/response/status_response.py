from pydantic import BaseModel
from typing import List


class StatusResponse(BaseModel):
    """API Status details"""
    status: str
    voice_engine: str
    registered_voices: int
    engines: List[str]
