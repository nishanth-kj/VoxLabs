"""The built-in model catalog and model defaults."""

from app.constants.model_backend import Backend
from app.constants.model_type import ModelType
from app.constants.voices import KOKORO_VOICES


# Backends that can synthesize speech in a cloned voice from reference samples.
CLONING_BACKENDS = (Backend.XTTS, Backend.F5, Backend.CHATTERBOX)
# Backends whose library downloads its own weights on first load, so installing means loading once.
FETCH_ON_LOAD_BACKENDS = (Backend.KOKORO, Backend.XTTS, Backend.F5, Backend.CHATTERBOX)

DEFAULT_TTS_MODEL = "piper-en-us-lessac-medium"
DEFAULT_CLONE_MODEL = "voice-profile-mfcc"
# Adds one engine's Python packages. `--inexact` keeps the engines already installed: a plain
# `uv sync --extra x` removes every other extra.
ENGINE_INSTALL_COMMAND = "uv sync --inexact --extra {extra}"

# Tried in this order when no model is requested and the default one is not installed.
FALLBACK_TTS_MODELS = ("chatterbox", "kokoro-82m", "piper-en-us-lessac-medium")

KOKORO_DEFAULT_VOICE = "af_heart"


def _hf(repo: str, path: str) -> str:
    """Direct Hugging Face file URL. The desktop app downloads these without the Python extra."""
    return f"https://huggingface.co/{repo}/resolve/main/{path}"


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
        "key": "kokoro-82m",
        "name": "Kokoro 82M",
        "model_type": ModelType.TTS,
        "backend": Backend.KOKORO,
        "version": "1.0",
        "size_mb": 330,
        "vram_mb": 1000,
        "online": False,
        "package": "kokoro",
        "extra": "kokoro",
        "capabilities": ["tts", "speed", "voices", "local"],
        "files": {
            "config.json": _hf("hexgrad/Kokoro-82M", "config.json"),
            "kokoro-v1_0.pth": _hf("hexgrad/Kokoro-82M", "kokoro-v1_0.pth"),
            **{
                f"voices/{voice['id']}.pt": _hf("hexgrad/Kokoro-82M", f"voices/{voice['id']}.pt")
                for voice in KOKORO_VOICES
            },
        },
    },
    {
        "key": "xtts-v2",
        "name": "Coqui XTTS v2",
        "model_type": ModelType.CLONE,
        "backend": Backend.XTTS,
        "version": "2.0.3",
        "size_mb": 2080,
        "vram_mb": 4000,
        "online": False,
        "package": "TTS",
        "extra": "xtts",
        "capabilities": ["tts", "clone", "multilingual", "temperature", "speed", "local"],
        "files": {
            "config.json": _hf("coqui/XTTS-v2", "config.json"),
            "vocab.json": _hf("coqui/XTTS-v2", "vocab.json"),
            "model.pth": _hf("coqui/XTTS-v2", "model.pth"),
            "dvae.pth": _hf("coqui/XTTS-v2", "dvae.pth"),
            "mel_stats.pth": _hf("coqui/XTTS-v2", "mel_stats.pth"),
            "speakers_xtts.pth": _hf("coqui/XTTS-v2", "speakers_xtts.pth"),
        },
    },
    {
        "key": "f5-tts",
        "name": "F5-TTS",
        "model_type": ModelType.CLONE,
        "backend": Backend.F5,
        "version": "1.0",
        "size_mb": 1400,
        "vram_mb": 3000,
        "online": False,
        "package": "f5_tts",
        "extra": "f5",
        "capabilities": ["tts", "clone", "speed", "seed", "local"],
        "files": {
            "model_1250000.safetensors": _hf("SWivid/F5-TTS", "F5TTS_v1_Base/model_1250000.safetensors"),
            "vocab.txt": _hf("SWivid/F5-TTS", "F5TTS_v1_Base/vocab.txt"),
            "vocos/config.yaml": _hf("charactr/vocos-mel-24khz", "config.yaml"),
            "vocos/pytorch_model.bin": _hf("charactr/vocos-mel-24khz", "pytorch_model.bin"),
        },
    },
    {
        "key": "chatterbox",
        "name": "Chatterbox TTS",
        "model_type": ModelType.CLONE,
        "backend": Backend.CHATTERBOX,
        "version": "0.1",
        "size_mb": 3200,
        "vram_mb": 4000,
        "online": False,
        "package": "chatterbox",
        "extra": "chatterbox",
        "capabilities": ["tts", "clone", "emotion", "temperature", "seed", "local"],
        "files": {
            "ve.safetensors": _hf("ResembleAI/chatterbox", "ve.safetensors"),
            "t3_cfg.safetensors": _hf("ResembleAI/chatterbox", "t3_cfg.safetensors"),
            "s3gen.safetensors": _hf("ResembleAI/chatterbox", "s3gen.safetensors"),
            "tokenizer.json": _hf("ResembleAI/chatterbox", "tokenizer.json"),
            "conds.pt": _hf("ResembleAI/chatterbox", "conds.pt"),
        },
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
