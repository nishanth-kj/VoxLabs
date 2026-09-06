from pydantic import BaseModel
from typing import Dict


class EmotionsResponse(BaseModel):
    """Emotions list response"""
    emotions: Dict[str, Dict[str, float]]
    count: int
