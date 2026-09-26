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
import threading
import urllib.request
import wave
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from app.constants.models import EDGE_DEFAULT_VOICE, ENGINE_INSTALL_COMMAND, KOKORO_DEFAULT_VOICE, Backend
from app.exceptions import ModelError
from app.utils import audio as audio_utils
from app.utils.logger import logger


@dataclass
class VoiceRef:
    """What a backend needs to speak in a particular voice."""

    sample_paths: list[str] = field(default_factory=list)
    language: str = "en"
    pitch_hz: float = 0.0
    engine_voice: str | None = None  # a built-in engine voice, e.g. Kokoro "af_heart" or an Edge short name


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
    # Longest text the engine speaks well in one call; None uses TTS_CHUNK_CHARS.
    max_chunk_chars: int | None = None

    def __init__(self, model_dir: Path, device: str = "cpu"):
        self.model_dir = Path(model_dir)
        self.device = device
        self.loaded = False
        # One generation at a time: GPU memory and these models are not safe to share between threads.
        self.lock = threading.Lock()

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


_download_guard = threading.Lock()
_download_locks: dict[str, threading.Lock] = {}


def _download_lock(dest: Path) -> threading.Lock:
    key = str(dest).lower()
    with _download_guard:
        lock = _download_locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _download_locks[key] = lock
        return lock


def _saved(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def _discard(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def download(url: str, dest: Path, progress: Callable[[float], None] | None = None,
             cancelled: Callable[[], bool] | None = None) -> Path:
    """Save `url` to `dest`. Hugging Face rejects some clients, so this sends a User-Agent
    and turns HTTP failures into a ModelError instead of a raw library exception.

    Two installs can ask for the same file. They share one lock, and a file Windows still
    has open is left alone when the other install already finished it.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    with _download_lock(dest):
        if _saved(dest):
            if progress:
                progress(1.0)
            return dest
        tmp = dest.with_name(f"{dest.name}.{threading.get_ident()}.part")
        last_error: Exception | None = None
        for _attempt in range(2):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "VoxLabs/3.0"})
                with urllib.request.urlopen(request, timeout=120) as response, open(tmp, "wb") as out:
                    total = int(response.headers.get("Content-Length") or 0)
                    done = 0
                    checked = False
                    while chunk := response.read(1 << 16):
                        if cancelled and cancelled():
                            raise ModelError("Download cancelled")
                        if not checked:
                            head = chunk.lstrip()[:15].lower()
                            if head.startswith(b"<!doctype") or head.startswith(b"<html"):
                                raise ModelError(f"Download of {dest.name} returned a web page instead of the file")
                            checked = True
                        out.write(chunk)
                        done += len(chunk)
                        if progress and total:
                            progress(min(done / total, 1.0))
                if done == 0:
                    raise ModelError(f"Download of {dest.name} was empty")
                tmp.replace(dest)
                return dest
            except ModelError:
                _discard(tmp)
                raise
            except Exception as exc:
                _discard(tmp)
                if _saved(dest):
                    if progress:
                        progress(1.0)
                    return dest
                last_error = exc
        raise ModelError(f"Could not download {dest.name}: {last_error}")


def apply_prosody(y: np.ndarray, sr: int, speed: float = 1.0, pitch: float = 1.0, energy: float = 1.0) -> np.ndarray:
    """Pitch shift / time stretch / gain (ported from the original EmotionalTTSEngine)."""
    if pitch and pitch > 0 and abs(pitch - 1.0) > 1e-3:
        y = audio_utils.pitch_shift(y, sr, 12 * np.log2(pitch))
    if speed and speed > 0 and abs(speed - 1.0) > 1e-3:
        y = audio_utils.time_stretch(y, speed)
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


def is_cuda_oom(exc: BaseException) -> bool:
    """True for torch's CUDA out-of-memory error, matched by name so torch is never imported here."""
    return type(exc).__name__ == "OutOfMemoryError" or "CUDA out of memory" in str(exc)


def free_cuda_memory() -> None:
    try:
        import torch  # pyright: ignore[reportMissingImports]

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


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
                    chunks.append(chunk.get("data") or b"")
            return b"".join(chunks)

        return _decode_bytes(asyncio.run(_run()))


# ---------------------------------------------------------------- local backends

class PiperBackend(ModelBackend):
    _voice: Any = None
    backend_id = Backend.PIPER
    native_params = frozenset({"speed"})

    def load(self):
        try:
            from piper import PiperVoice  # pyright: ignore[reportMissingImports]
        except ImportError as exc:
            raise ModelError(f"Piper is not installed. Run: {ENGINE_INSTALL_COMMAND.format(extra='piper')}") from exc
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
                from piper import SynthesisConfig  # pyright: ignore[reportMissingImports]

                self._voice.synthesize_wav(request.text, wav_file, syn_config=SynthesisConfig(length_scale=length_scale))
            except ImportError:  # piper-tts 1.2
                self._voice.synthesize(request.text, wav_file, length_scale=length_scale)
        return _decode_bytes(buf.getvalue())


class KokoroBackend(ModelBackend):
    """Kokoro 82M (hexgrad, Apache-2.0): small and fast, fine on CPU. Built-in voices only, picked with
    `engine_voice` (af_heart, af_bella, bm_george, ...); the first letter is the language."""

    REPO = "hexgrad/Kokoro-82M"
    SAMPLE_RATE = 24000

    _model: Any = None
    backend_id = Backend.KOKORO
    native_params = frozenset({"speed"})
    # KPipeline splits long input itself; this only bounds one call.
    max_chunk_chars = 500

    def load(self):
        try:
            from kokoro import KModel  # pyright: ignore[reportMissingImports]
        except ImportError as exc:
            raise ModelError(f"Kokoro is not installed. Run: {ENGINE_INSTALL_COMMAND.format(extra='kokoro')}") from exc
        os.environ.setdefault("HF_HOME", str(self.model_dir))
        config = self.model_dir / "config.json"
        weights = self.model_dir / "kokoro-v1_0.pth"
        if config.is_file() and weights.is_file():
            self._model = KModel(repo_id=self.REPO, config=str(config), model=str(weights)).to(self.device).eval()
        else:
            self._model = KModel(repo_id=self.REPO).to(self.device).eval()
        self._pipelines: dict[str, Any] = {}
        self.loaded = True

    def unload(self):
        self._model = None
        self._pipelines = {}
        self.loaded = False

    def synthesize(self, request, voice):
        from kokoro import KPipeline  # pyright: ignore[reportMissingImports]

        name = (voice.engine_voice if voice else None) or KOKORO_DEFAULT_VOICE
        lang = name[0]
        if lang not in self._pipelines:
            self._pipelines[lang] = KPipeline(lang_code=lang, repo_id=self.REPO, model=self._model)
        voice_file = self.model_dir / "voices" / f"{name}.pt"
        voice_arg = str(voice_file) if voice_file.is_file() else name
        try:
            results = self._pipelines[lang](request.text, voice=voice_arg, speed=request.speed)
            parts = [r.audio.detach().cpu().numpy() for r in results if r.audio is not None]
        except Exception as exc:
            if type(exc).__name__ in ("EntryNotFoundError", "RemoteEntryNotFoundError"):
                raise ModelError(f"Kokoro has no voice '{name}'", field="engine_voice") from exc
            raise
        if not parts:
            raise ModelError("Kokoro returned no audio for this text")
        return np.concatenate(parts).astype(np.float32), self.SAMPLE_RATE


class XTTSBackend(ModelBackend):
    _tts: Any = None
    backend_id = Backend.XTTS
    supports_cloning = True
    native_params = frozenset({"speed", "temperature"})

    def load(self):
        try:
            from TTS.api import TTS  # pyright: ignore[reportMissingImports]
        except ImportError as exc:
            raise ModelError(f"XTTS is not installed. Run: {ENGINE_INSTALL_COMMAND.format(extra='xtts')}") from exc
        model_path = self.model_dir / "model.pth"
        config_path = self.model_dir / "config.json"
        if model_path.is_file() and config_path.is_file():
            self._tts = TTS(model_path=str(model_path), config_path=str(config_path)).to(self.device)
        else:
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
        wav = self._tts.tts(text=request.text, speaker_wav=refs, language=(voice.language if voice else None) or "en", **kwargs)
        return _torch_to_numpy(wav), int(self._tts.synthesizer.output_sample_rate)


class F5Backend(ModelBackend):
    _f5: Any = None
    backend_id = Backend.F5
    supports_cloning = True
    native_params = frozenset({"speed"})

    def load(self):
        try:
            from f5_tts.api import F5TTS  # pyright: ignore[reportMissingImports]
        except ImportError as exc:
            raise ModelError(f"F5-TTS is not installed. Run: {ENGINE_INSTALL_COMMAND.format(extra='f5')}") from exc
        os.environ.setdefault("HF_HOME", str(self.model_dir))
        kwargs: dict[str, Any] = {"device": self.device}
        checkpoint = self.model_dir / "model_1250000.safetensors"
        vocab = self.model_dir / "vocab.txt"
        vocoder = self.model_dir / "vocos"
        if checkpoint.is_file():
            kwargs["ckpt_file"] = str(checkpoint)
        if vocab.is_file():
            kwargs["vocab_file"] = str(vocab)
        if (vocoder / "config.yaml").is_file() and (vocoder / "pytorch_model.bin").is_file():
            kwargs["vocoder_local_path"] = str(vocoder)
        self._f5 = F5TTS(**kwargs)
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
    """Chatterbox (Resemble AI, MIT). Speaks in its built-in voice, or clones the voice's first sample."""

    _model: Any = None
    backend_id = Backend.CHATTERBOX
    supports_cloning = True
    native_params = frozenset({"temperature", "emotion"})
    # Chatterbox starts to drift or cut off past a couple of sentences.
    max_chunk_chars = 280

    def load(self):
        try:
            from chatterbox.tts import ChatterboxTTS  # pyright: ignore[reportMissingImports]
        except ImportError as exc:
            raise ModelError(f"Chatterbox is not installed. Run: {ENGINE_INSTALL_COMMAND.format(extra='chatterbox')}") from exc
        weights = ("ve.safetensors", "t3_cfg.safetensors", "s3gen.safetensors", "tokenizer.json", "conds.pt")
        if all((self.model_dir / name).is_file() for name in weights):
            self._model = ChatterboxTTS.from_local(self.model_dir, self.device)
        else:
            os.environ.setdefault("HF_HOME", str(self.model_dir))
            self._model = ChatterboxTTS.from_pretrained(device=self.device)
        self._builtin_conds = self._model.conds
        self._sample_conds: dict[tuple[str, float], Any] = {}
        self.loaded = True

    def unload(self):
        self._model = None
        self._builtin_conds = None
        self._sample_conds = {}
        self.loaded = False

    def synthesize(self, request, voice):
        if request.seed is not None:
            import torch  # pyright: ignore[reportMissingImports]

            torch.manual_seed(request.seed)
        exaggeration = {"neutral": 0.5, "calm": 0.3, "sad": 0.4}.get(request.emotion, 0.7)
        # generate(audio_prompt_path=...) replaces the model's current voice, so the conditionals for
        # each sample are prepared once and swapped in explicitly.
        self._model.conds = self._conds(voice, exaggeration)
        wav = self._model.generate(
            request.text, exaggeration=exaggeration,
            cfg_weight=0.6 if request.emotion == "calm" else 0.5,
            temperature=request.temperature if request.temperature is not None else 0.8,
        )
        return _torch_to_numpy(wav), int(self._model.sr)

    def _conds(self, voice: VoiceRef | None, exaggeration: float) -> Any:
        if not voice or not voice.sample_paths:
            return self._builtin_conds
        sample = Path(voice.sample_paths[0])
        key = (str(sample.resolve()), sample.stat().st_mtime)
        if key not in self._sample_conds:
            self._model.prepare_conditionals(str(sample), exaggeration=exaggeration)
            self._sample_conds[key] = self._model.conds
        return self._sample_conds[key]


_BACKENDS: dict[str, type[ModelBackend]] = {
    Backend.EMOTIONAL: EmotionalBackend,
    Backend.EDGE: EdgeBackend,
    Backend.PIPER: PiperBackend,
    Backend.KOKORO: KokoroBackend,
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
