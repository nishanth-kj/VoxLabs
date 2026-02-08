from pydantic import BaseModel
from typing import Dict, List, Any, Optional

class APIResponse(BaseModel):
    """Standardized API Response wrapper"""
    status: int
    data: Optional[Any] = None
    error: Optional[str] = None

class StatusResponse(BaseModel):
    """API Status details"""
    status: str
    voice_engine: str
    registered_voices: int
    engines: List[str]

class EmotionsResponse(BaseModel):
    """Emotions list response"""
    emotions: Dict[str, Dict[str, float]]
    count: int
