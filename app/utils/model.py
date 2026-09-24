"""AI model backends behind one small interface.

Each backend turns text (+ optional reference voice) into float32 audio. Heavy
libraries are imported lazily inside `load()` so the base install stays light
and a missing optional extra only disables that one backend.

ModelService decides *which* backend to use and when to load it; this module
only knows *how* to talk to each engine.
"""

import asyncio
import importlib.util
import io
import os
import urllib.request
import wave
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

from app.constants.models import EDGE_DEFAULT_VOICE, Backend
from app.exceptions import ModelError
from app.utils import audio as audio_utils
from app.utils.logger import logger


@dataclass
class VoiceRef:
    """What a backend needs to speak in a particular voice."""

    sample_paths: list[str] = field(default_factory=list)
    language: str = "en"
    pitch_hz: float = 0.0
    engine_voice: str | None = None  # e.g. an Edge voice short name


@dataclass
class SynthesisRequest:
    text: str
    language: str = "en"
    speed: float = 1.0
    pitch: float = 1.0
    energy: float = 1.0
    emotion: str = "neutral"
    style: str = "default"
    temperature: float | None = None
    seed: int | None = None


class ModelBackend:
    backend_id = ""
    online = False
    supports_cloning = False
    # Parameters the engine handles itself; the rest are applied with DSP afterwards.
    native_params: frozenset[str] = frozenset()

    def __init__(self, model_dir: Path, device: str = "cpu"):
        self.model_dir = Path(model_dir)
        self.device = device
        self.loaded = False

    def load(self) -> None:
        self.loaded = True

    def unload(self) -> None:
        self.loaded = False

    def synthesize(self, request: SynthesisRequest, voice: VoiceRef | None) -> tuple[np.ndarray, int]:
        raise NotImplementedError

    def _require_reference(self, voice: VoiceRef | None) -> list[str]:
        if not voice or not voice.sample_paths:
            raise ModelError(f"{self.backend_id} needs a cloned voice with at least one sample")
        return voice.sample_paths


# ---------------------------------------------------------------- helpers

def package_installed(package: str | None) -> bool:
    if not package:
        return True
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


def download(url: str, dest: Path, progress: Callable[[float], None] | None = None,
             cancelled: Callable[[], bool] | None = None) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=60) as response, open(tmp, "wb") as out:
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        while chunk := response.read(1 << 16):
            if cancelled and cancelled():
                out.close()
                tmp.unlink(missing_ok=True)
                raise ModelError("Download cancelled")
            out.write(chunk)
            done += len(chunk)
            if progress and total:
                progress(done / total)
    tmp.replace(dest)
    return dest


def apply_prosody(y: np.ndarray, sr: int, speed: float = 1.0, pitch: float = 1.0, energy: float = 1.0) -> np.ndarray:
    """Pitch shift / time stretch / gain (ported from the original EmotionalTTSEngine)."""
    import librosa

    if pitch and pitch > 0 and abs(pitch - 1.0) > 1e-3:
        y = librosa.effects.pitch_shift(y, sr=sr, n_steps=12 * np.log2(pitch))
    if speed and speed > 0 and abs(speed - 1.0) > 1e-3:
        y = librosa.effects.time_stretch(y, rate=speed)
    if energy and energy > 0 and abs(energy - 1.0) > 1e-3:
        y = y * energy
        peak = float(np.abs(y).max()) if y.size else 0.0
        if peak > 1.0:
            y = y / peak
    return y.astype(np.float32)


def extract_voice_profile(path: str | Path) -> dict:
    """MFCC + pitch voice profile (ported from VoiceEngine.extract_voice_features)."""
    import librosa

    y, sr = audio_utils.load(path, sr=22050)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return {
        "mfcc_mean": mfcc.mean(axis=1).round(4).tolist(),
        "mfcc_std": np.std(mfcc, axis=1).round(4).tolist(),
        "pitch_hz": round(audio_utils.estimate_pitch_hz(y, sr), 2),
    }


def _decode_bytes(data: bytes) -> tuple[np.ndarray, int]:
    y, sr = sf.read(io.BytesIO(data), dtype="float32", always_2d=False)
    return audio_utils.to_mono(y), int(sr)


def _torch_to_numpy(wav) -> np.ndarray:
    if hasattr(wav, "detach"):
        wav = wav.detach().cpu().numpy()
    return np.asarray(wav, dtype=np.float32).squeeze()


# ---------------------------------------------------------------- online backends (opt-in)

class EmotionalBackend(ModelBackend):
    """gTTS speech; emotion/speed/pitch are shaped afterwards with librosa. Sends text to Google."""

    backend_id = Backend.EMOTIONAL
    online = True

    def synthesize(self, request, voice):
        from gtts import gTTS

        buf = io.BytesIO()
        gTTS(text=request.text, lang=(voice.language if voice else request.language) or "en").write_to_fp(buf)
        return _decode_bytes(buf.getvalue())


class EdgeBackend(ModelBackend):
    """Microsoft Edge neural voices. Sends text to Microsoft."""

    backend_id = Backend.EDGE
    online = True
    native_params = frozenset({"speed", "pitch"})

    def synthesize(self, request, voice):
        import edge_tts

        voice_name = (voice.engine_voice if voice else None) or EDGE_DEFAULT_VOICE
        rate = f"{round((request.speed - 1.0) * 100):+d}%"
        pitch = f"{round((request.pitch - 1.0) * 100):+d}Hz"

        async def _run() -> bytes:
            communicate = edge_tts.Communicate(request.text, voice_name, rate=rate, pitch=pitch)
            chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            return b"".join(chunks)

        return _decode_bytes(asyncio.run(_run()))


# ---------------------------------------------------------------- local backends

class PiperBackend(ModelBackend):
    backend_id = Backend.PIPER
    native_params = frozenset({"speed"})

    def load(self):
        try:
            from piper import PiperVoice
        except ImportError as exc:
            raise ModelError("Piper is not installed. Run: uv sync --extra piper") from exc
        model_path = self.model_dir / "model.onnx"
        if not model_path.exists():
            raise ModelError("Piper voice files are missing. Install the model first.")
        self._voice = PiperVoice.load(str(model_path), config_path=str(model_path) + ".json",
                                      use_cuda=self.device.startswith("cuda"))
        self.loaded = True

    def unload(self):
        self._voice = None
        self.loaded = False

    def synthesize(self, request, voice):
        length_scale = 1.0 / max(request.speed, 0.1)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            try:  # piper-tts >= 1.3
                from piper import SynthesisConfig

                self._voice.synthesize_wav(request.text, wav_file, syn_config=SynthesisConfig(length_scale=length_scale))
            except ImportError:  # piper-tts 1.2
                self._voice.synthesize(request.text, wav_file, length_scale=length_scale)
        return _decode_bytes(buf.getvalue())


class XTTSBackend(ModelBackend):
    backend_id = Backend.XTTS
    supports_cloning = True
    native_params = frozenset({"speed", "temperature"})

    def load(self):
        try:
            from TTS.api import TTS
        except ImportError as exc:
            raise ModelError("XTTS is not installed. Run: uv sync --extra xtts") from exc
        os.environ.setdefault("TTS_HOME", str(self.model_dir))
        self._tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        self.loaded = True

    def unload(self):
        self._tts = None
        self.loaded = False

    def synthesize(self, request, voice):
        refs = self._require_reference(voice)
        kwargs = {"speed": request.speed}
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        wav = self._tts.tts(text=request.text, speaker_wav=refs, language=voice.language or "en", **kwargs)
        return _torch_to_numpy(wav), int(self._tts.synthesizer.output_sample_rate)


class F5Backend(ModelBackend):
    backend_id = Backend.F5
    supports_cloning = True
    native_params = frozenset({"speed"})

    def load(self):
        try:
            from f5_tts.api import F5TTS
        except ImportError as exc:
            raise ModelError("F5-TTS is not installed. Run: uv sync --extra f5") from exc
        os.environ.setdefault("HF_HOME", str(self.model_dir))
        self._f5 = F5TTS(device=self.device)
        self.loaded = True

    def unload(self):
        self._f5 = None
        self.loaded = False

    def synthesize(self, request, voice):
        refs = self._require_reference(voice)
        wav, sr, _ = self._f5.infer(
            ref_file=refs[0], ref_text="", gen_text=request.text, speed=request.speed,
            seed=request.seed if request.seed is not None else -1,
        )
        return _torch_to_numpy(wav), int(sr)


class ChatterboxBackend(ModelBackend):
    backend_id = Backend.CHATTERBOX
    supports_cloning = True
    native_params = frozenset({"temperature", "emotion"})

    def load(self):
        try:
            from chatterbox.tts import ChatterboxTTS
        except ImportError as exc:
            raise ModelError("Chatterbox is not installed. Run: uv sync --extra chatterbox") from exc
        os.environ.setdefault("HF_HOME", str(self.model_dir))
        self._model = ChatterboxTTS.from_pretrained(device=self.device)
        self.loaded = True

    def unload(self):
        self._model = None
        self.loaded = False

    def synthesize(self, request, voice):
        refs = self._require_reference(voice)
        if request.seed is not None:
            import torch

            torch.manual_seed(request.seed)
        exaggeration = {"neutral": 0.5, "calm": 0.3, "sad": 0.4}.get(request.emotion, 0.7)
        wav = self._model.generate(
            request.text, audio_prompt_path=refs[0], exaggeration=exaggeration,
            temperature=request.temperature if request.temperature is not None else 0.8,
        )
        return _torch_to_numpy(wav), int(self._model.sr)


_BACKENDS: dict[str, type[ModelBackend]] = {
    Backend.EMOTIONAL: EmotionalBackend,
    Backend.EDGE: EdgeBackend,
    Backend.PIPER: PiperBackend,
    Backend.XTTS: XTTSBackend,
    Backend.F5: F5Backend,
    Backend.CHATTERBOX: ChatterboxBackend,
}


def register_backend(backend_id: str, cls: type[ModelBackend]) -> None:
    """Add or replace a backend (used by tests and future engines)."""
    _BACKENDS[backend_id] = cls


def backend_class(backend_id: str) -> type[ModelBackend] | None:
    return _BACKENDS.get(backend_id)


def create_backend(backend_id: str, model_dir: Path, device: str) -> ModelBackend:
    cls = backend_class(backend_id)
    if cls is None:
        raise ModelError(f"Backend '{backend_id}' cannot synthesize speech")
    logger.info(f"Creating backend {backend_id} on {device}")
    return cls(model_dir, device)
