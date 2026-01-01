"""
VoxLabs Voice Engine Package
Advanced voice cloning and emotional TTS system
"""

import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Import from backend
from voice_engine import VoiceEngine, VoiceIdentity, get_voice_engine

# Import emotional TTS
from .emotional_tts import EmotionalTTSEngine

__all__ = [
    'VoiceEngine',
    'VoiceIdentity',
    'get_voice_engine',
    'EmotionalTTSEngine'
]

__version__ = '2.0.0'
