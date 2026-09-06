from pydantic import BaseModel
from typing import Dict


class VoiceIdentityModel(BaseModel):
    """Frontend-safe Voice Identity"""
    voice_id: str
    name: str
    consent: bool
    created_at: str
    project_id: str
    metadata: Dict
    revoked: bool
