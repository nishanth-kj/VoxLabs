from pydantic import BaseModel
from typing import List, Optional, Dict

class VoiceIdentityModel(BaseModel):
    """Frontend-safe Voice Identity"""
    voice_id: str
    name: str
    consent: bool
    created_at: str
    project_id: str
    metadata: Dict
    revoked: bool

class VoiceListResponse(BaseModel):
    """List of voices response"""
    voices: List[VoiceIdentityModel]
    count: int

class VoiceRegistrationResponse(BaseModel):
    """Successful registration response"""
    voice_id: str
    name: str
    message: str
