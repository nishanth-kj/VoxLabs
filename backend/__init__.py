"""
VoxLabs Backend Package
FastAPI backend for voice cloning and TTS
"""

from .voice_engine import VoiceEngine, VoiceIdentity, get_voice_engine

__all__ = [
    'VoiceEngine',
    'VoiceIdentity',
    'get_voice_engine'
]

__version__ = '2.0.0'
