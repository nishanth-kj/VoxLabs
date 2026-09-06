from pydantic import BaseModel
from typing import List

from .voice_identity_response import VoiceIdentityModel


class VoiceListResponse(BaseModel):
    """List of voices response"""
    voices: List[VoiceIdentityModel]
    count: int
