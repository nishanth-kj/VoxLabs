"""The built-in model catalog and model defaults."""

from app.constants.model_backend import Backend
from app.constants.model_type import ModelType


# Backends that can synthesize speech in a cloned voice from reference samples.
CLONING_BACKENDS = (Backend.XTTS, Backend.F5, Backend.CHATTERBOX)

DEFAULT_TTS_MODEL = "piper-en-us-lessac-medium"
DEFAULT_CLONE_MODEL = "voice-profile-mfcc"

# Every model VoxLabs knows about. `package` is the import that must succeed for
# the backend to work; `extra` is the uv extra that installs it.
MODEL_CATALOG = [
    {
        "key": "piper-en-us-lessac-medium",
        "name": "Piper · en_US Lessac (medium)",
        "model_type": ModelType.TTS,
        "backend": Backend.PIPER,
        "version": "1.0",
        "size_mb": 63,
        "vram_mb": 0,
        "online": False,
        "package": "piper",
        "extra": "piper",
        "capabilities": ["tts", "speed", "local"],
        "files": {
            "model.onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
            "model.onnx.json": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        },
    },
    {
        "key": "xtts-v2",
        "name": "Coqui XTTS v2",
        "model_type": ModelType.CLONE,
        "backend": Backend.XTTS,
        "version": "2.0.3",
        "size_mb": 1870,
        "vram_mb": 4000,
        "online": False,
        "package": "TTS",
        "extra": "xtts",
        "capabilities": ["tts", "clone", "multilingual", "temperature", "speed", "local"],
    },
    {
        "key": "f5-tts",
        "name": "F5-TTS",
        "model_type": ModelType.CLONE,
        "backend": Backend.F5,
        "version": "1.0",
        "size_mb": 1350,
        "vram_mb": 3000,
        "online": False,
        "package": "f5_tts",
        "extra": "f5",
        "capabilities": ["tts", "clone", "speed", "seed", "local"],
    },
    {
        "key": "chatterbox",
        "name": "Chatterbox TTS",
        "model_type": ModelType.CLONE,
        "backend": Backend.CHATTERBOX,
        "version": "0.1",
        "size_mb": 2100,
        "vram_mb": 4000,
        "online": False,
        "package": "chatterbox",
        "extra": "chatterbox",
        "capabilities": ["tts", "clone", "emotion", "temperature", "seed", "local"],
    },
    {
        "key": "voice-profile-mfcc",
        "name": "VoxLabs voice profile (MFCC)",
        "model_type": ModelType.EMBED,
        "backend": Backend.MFCC,
        "version": "1.0",
        "size_mb": 0,
        "vram_mb": 0,
        "online": False,
        "package": "librosa",
        "extra": None,
        "capabilities": ["embed", "clone", "local"],
    },
    {
        "key": "dsp-enhance",
        "name": "VoxLabs DSP enhancement",
        "model_type": ModelType.ENHANCE,
        "backend": Backend.DSP,
        "version": "1.0",
        "size_mb": 0,
        "vram_mb": 0,
        "online": False,
        "package": "scipy",
        "extra": None,
        "capabilities": ["denoise", "eq", "compress", "limit", "loudness", "local"],
    },
    {
        "key": "gtts-emotional",
        "name": "Emotional TTS (Google, online)",
        "model_type": ModelType.TTS,
        "backend": Backend.EMOTIONAL,
        "version": "2.1",
        "size_mb": 0,
        "vram_mb": 0,
        "online": True,
        "package": "gtts",
        "extra": None,
        "capabilities": ["tts", "emotion", "speed", "pitch", "online"],
    },
    {
        "key": "edge-neural",
        "name": "Microsoft Edge neural voices (online)",
        "model_type": ModelType.TTS,
        "backend": Backend.EDGE,
        "version": "6",
        "size_mb": 0,
        "vram_mb": 0,
        "online": True,
        "package": "edge_tts",
        "extra": None,
        "capabilities": ["tts", "speed", "pitch", "locales", "online"],
    },
]

EDGE_DEFAULT_VOICE = "en-US-AriaNeural"
