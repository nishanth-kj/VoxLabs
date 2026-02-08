import pytest
import sys
from pathlib import Path

# Add api directory to path to import engine from the correct location
# Path(__file__).parents[1] is the root C:\Projects\VoxLabs\api
sys.path.insert(0, str(Path(__file__).parents[1]))

from services.tts_service import EmotionalTTSEngine

@pytest.fixture
def engine():
    return EmotionalTTSEngine()

def test_engine_initialization(engine):
    """Verify the engine initializes and provides emotions."""
    assert engine is not None
    emotions = engine.get_emotions()
    assert isinstance(emotions, dict)
    assert "happy" in emotions
    assert "neutral" in emotions

def test_emotion_presets(engine):
    """Verify that specific emotions have the expected modulation parameters."""
    emotions = engine.get_emotions()
    
    # Happy: faster and higher pitch
    happy = emotions["happy"]
    assert happy["speed"] > 1.0
    assert happy["pitch"] > 1.0
    
    # Sad: slower and lower energy
    sad = emotions["sad"]
    assert sad["speed"] < 1.0
    assert sad["energy"] < 1.0
    # Note: pitch for sad in tts_service.py is 0.9 ( < 1.0)

def test_get_emotions_content(engine):
    """Checks if the returned emotions dict contains the required keys."""
    emotions = engine.get_emotions()
    for emotion, params in emotions.items():
        assert "speed" in params
        assert "pitch" in params
        assert "energy" in params
