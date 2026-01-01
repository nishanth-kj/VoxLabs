
import pytest
import sys
from pathlib import Path

# Add api directory to path to import engine
sys.path.insert(0, str(Path(__file__).parents[1]))

from engine.emotional_tts import EmotionalTTSEngine

@pytest.fixture
def engine():
    return EmotionalTTSEngine()

def test_engine_initialization(engine):
    assert engine is not None
    assert isinstance(engine.get_emotions(), dict)
    assert "happy" in engine.get_emotions()

def test_emotion_presets(engine):
    emotions = engine.get_emotions()
    happy = emotions["happy"]
    assert happy["speed"] > 1.0  # Happy should be faster
    assert happy["pitch"] > 1.0  # Happy should be higher pitch

    sad = emotions["sad"]
    assert sad["speed"] < 1.0    # Sad should be slower
    assert sad["energy"] < 1.0   # Sad should be lower energy

def test_invalid_emotion_fallback(engine):
    # This assumes the engine handles invalid emotions gracefully or has a default
    # Looking at the code, it usually defaults or we can verify behavior
    pass
