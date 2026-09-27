"""The built-in model catalog and model defaults."""

from app.constants.model_backend import Backend
from app.constants.model_type import ModelType
from app.constants.voices import KOKORO_VOICES


# Backends that can synthesize speech in a cloned voice from reference samples.
CLONING_BACKENDS = (Backend.CHATTERBOX, Backend.CHATTERBOX_TURBO, Backend.QWEN3)
# Backends whose library downloads its own weights on first load, so installing means loading once.
FETCH_ON_LOAD_BACKENDS = (Backend.KOKORO, Backend.CHATTERBOX, Backend.CHATTERBOX_TURBO)

DEFAULT_TTS_MODEL = "piper-en-us-lessac-medium"
DEFAULT_CLONE_MODEL = "voice-profile-mfcc"
# Adds one engine's Python packages. `--inexact` keeps the engines already installed: a plain
# `uv sync --extra x` removes every other extra.
ENGINE_INSTALL_COMMAND = "uv sync --inexact --extra {extra}"

# Tried in this order when no model is requested and the default one is not installed.
FALLBACK_TTS_MODELS = ("chatterbox", "chatterbox-turbo", "kokoro-82m", "piper-en-us-lessac-medium")

KOKORO_DEFAULT_VOICE = "af_heart"

# Engines whose libraries cannot share VoxLabs' environment get their own under data/engines/<name>,
# set up with uv when the model is installed, and run as a helper process (app/utils/engine_workers/).
# qwen-tts 0.1.1 pins transformers 4.57.3, and Chatterbox pins 5.2.0.
ENGINE_ENVIRONMENTS = {
    "qwen3-tts": {
        "requirements": ("qwen-tts==0.1.1", "torch==2.6.0", "torchaudio==2.6.0", "soundfile>=0.12.1"),
        "module": "qwen_tts",
        "worker": "qwen3_worker.py",
    },
}


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
        # Faster Chatterbox (MIT). Same engine package; clones from a sample longer than 5 seconds.
        "key": "chatterbox-turbo",
        "name": "Chatterbox Turbo",
        "model_type": ModelType.CLONE,
        "backend": Backend.CHATTERBOX_TURBO,
        "version": "turbo-v1",
        "size_mb": 2990,
        "vram_mb": 3000,
        "online": False,
        "package": "chatterbox",
        "extra": "chatterbox",
        "capabilities": ["tts", "clone", "temperature", "seed", "local"],
        "files": {
            "ve.safetensors": _hf("ResembleAI/chatterbox-turbo", "ve.safetensors"),
            "t3_turbo_v1.safetensors": _hf("ResembleAI/chatterbox-turbo", "t3_turbo_v1.safetensors"),
            "s3gen_meanflow.safetensors": _hf("ResembleAI/chatterbox-turbo", "s3gen_meanflow.safetensors"),
            "conds.pt": _hf("ResembleAI/chatterbox-turbo", "conds.pt"),
            "vocab.json": _hf("ResembleAI/chatterbox-turbo", "vocab.json"),
            "merges.txt": _hf("ResembleAI/chatterbox-turbo", "merges.txt"),
            "tokenizer_config.json": _hf("ResembleAI/chatterbox-turbo", "tokenizer_config.json"),
            "special_tokens_map.json": _hf("ResembleAI/chatterbox-turbo", "special_tokens_map.json"),
            "added_tokens.json": _hf("ResembleAI/chatterbox-turbo", "added_tokens.json"),
        },
    },
    {
        # Qwen3-TTS (Alibaba Qwen, Apache-2.0). Clones any voice sample; it has no built-in voice.
        # Its library needs another transformers version, so it runs in its own engine environment.
        "key": "qwen3-tts-0.6b",
        "name": "Qwen3-TTS 0.6B",
        "model_type": ModelType.CLONE,
        "backend": Backend.QWEN3,
        "version": "12hz-0.6b-base",
        "size_mb": 2400,
        "vram_mb": 3000,
        "online": False,
        "package": None,
        "extra": None,
        "environment": "qwen3-tts",
        "capabilities": ["tts", "clone", "temperature", "seed", "local"],
        "files": {
            name: _hf("Qwen/Qwen3-TTS-12Hz-0.6B-Base", name)
            for name in ("config.json", "generation_config.json", "model.safetensors", "preprocessor_config.json",
                         "tokenizer_config.json", "vocab.json", "merges.txt", "speech_tokenizer/config.json",
                         "speech_tokenizer/configuration.json", "speech_tokenizer/model.safetensors",
                         "speech_tokenizer/preprocessor_config.json")
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
