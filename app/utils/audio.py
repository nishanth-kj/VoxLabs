"""Low-level audio primitives: I/O, inspection and DSP building blocks.

Everything works on mono or multi-channel float32 numpy arrays shaped
(samples,) or (samples, channels). Workflow decisions live in AudioService.
"""

from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

from app.constants.audio import AI_GENERATED_TAG, SOUNDFILE_FORMATS
from app.exceptions import AudioError
from app.utils import ffmpeg
from app.utils.files import extension, file_size

EPS = 1e-10


# ---------------------------------------------------------------- I/O

def load(path: str | Path, sr: int | None = None, mono: bool = True) -> tuple[np.ndarray, int]:
    """Decode an audio file to float32. Falls back to FFmpeg for m4a/aac/etc."""
    path = Path(path)
    if not path.exists():
        raise AudioError(f"Audio file not found: {path.name}")
    try:
        y, file_sr = sf.read(str(path), dtype="float32", always_2d=False)
    except Exception:
        if not ffmpeg.available():
            raise AudioError(f"Cannot decode {path.name}: unsupported format and FFmpeg is not installed")
        y, file_sr = ffmpeg.decode(path)
    if mono and y.ndim > 1:
        y = y.mean(axis=1)
    if sr and sr != file_sr:
        y = resample(y, file_sr, sr)
        file_sr = sr
    return y.astype(np.float32, copy=False), int(file_sr)


def save(
    path: str | Path,
    y: np.ndarray,
    sr: int,
    fmt: str | None = None,
    ai_generated: bool = False,
) -> Path:
    """Encode audio. WAV/FLAC/OGG/MP3 via libsndfile, anything else via FFmpeg."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = (fmt or extension(path) or "wav").lower()
    y = np.clip(np.nan_to_num(y), -1.0, 1.0).astype(np.float32)
    if fmt in SOUNDFILE_FORMATS:
        subtype = {"wav": "PCM_16", "flac": "PCM_16", "ogg": "VORBIS", "mp3": "MPEG_LAYER_III"}[fmt]
        channels = 1 if y.ndim == 1 else y.shape[1]
        try:
            with sf.SoundFile(
                str(path), "w", samplerate=sr, channels=channels, format=SOUNDFILE_FORMATS[fmt], subtype=subtype
            ) as fh:
                _tag(fh, ai_generated)
                fh.write(y)
            return path
        except Exception as exc:
            path.unlink(missing_ok=True)
            if not ffmpeg.available():
                raise AudioError(f"Could not write {fmt.upper()}: {exc}")
    if not ffmpeg.available():
        raise AudioError(f"Exporting {fmt.upper()} requires FFmpeg on PATH")
    tmp = path.with_suffix(".tmp.wav")
    save(tmp, y, sr, "wav")
    try:
        ffmpeg.convert(tmp, path, metadata={"comment": AI_GENERATED_TAG} if ai_generated else None)
    finally:
        tmp.unlink(missing_ok=True)
    return path


def _tag(fh: sf.SoundFile, ai_generated: bool) -> None:
    try:
        fh.software = "VoxLabs"
        if ai_generated:
            fh.comment = AI_GENERATED_TAG
    except Exception:
        pass  # not every container supports string metadata


def read_tags(path: str | Path) -> dict:
    try:
        with sf.SoundFile(str(path)) as fh:
            return {k: v for k, v in fh.copy_metadata().items() if v}
    except Exception:
        return {}


def info(path: str | Path) -> dict:
    """Metadata without decoding the whole file."""
    path = Path(path)
    try:
        meta = sf.info(str(path))
        return {
            "duration": float(meta.duration),
            "sample_rate": int(meta.samplerate),
            "channels": int(meta.channels),
            "format": extension(path),
            "codec": meta.subtype,
            "file_size": file_size(path),
        }
    except Exception:
        if ffmpeg.available():
            probed = ffmpeg.probe(path)
            probed["file_size"] = file_size(path)
            return probed
        raise AudioError(f"Cannot read audio metadata for {path.name}")


# ---------------------------------------------------------------- inspection

def duration(y: np.ndarray, sr: int) -> float:
    return len(y) / float(sr) if sr else 0.0


def to_mono(y: np.ndarray) -> np.ndarray:
    return y.mean(axis=1) if y.ndim > 1 else y


def peak_db(y: np.ndarray) -> float:
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    return 20 * np.log10(peak + EPS)


def rms_db(y: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(np.square(y)))) if y.size else 0.0
    return 20 * np.log10(rms + EPS)


def frame_rms_db(y: np.ndarray, sr: int, frame_ms: float = 20.0) -> np.ndarray:
    mono = to_mono(y)
    frame = max(1, int(sr * frame_ms / 1000))
    n = len(mono) // frame
    if n == 0:
        return np.array([rms_db(mono)])
    frames = mono[: n * frame].reshape(n, frame)
    return 20 * np.log10(np.sqrt(np.mean(frames**2, axis=1)) + EPS)


def silence_ratio(y: np.ndarray, sr: int, threshold_db: float) -> float:
    levels = frame_rms_db(y, sr)
    return float(np.mean(levels < threshold_db)) if levels.size else 1.0


def clipping_ratio(y: np.ndarray, level: float) -> float:
    return float(np.mean(np.abs(y) >= level)) if y.size else 0.0


def waveform_peaks(y: np.ndarray, buckets: int) -> np.ndarray:
    """(buckets, 2) array of min/max per bucket for drawing a waveform."""
    mono = to_mono(y)
    if mono.size == 0 or buckets <= 0:
        return np.zeros((max(buckets, 0), 2), dtype=np.float32)
    edges = np.linspace(0, mono.size, buckets + 1).astype(int)
    out = np.zeros((buckets, 2), dtype=np.float32)
    for i in range(buckets):
        chunk = mono[edges[i] : max(edges[i + 1], edges[i] + 1)]
        out[i] = (chunk.min(), chunk.max())
    return out


def estimate_pitch_hz(y: np.ndarray, sr: int) -> float:
    """Median fundamental frequency of voiced frames (0 if unvoiced)."""
    import librosa

    mono = to_mono(y)
    if mono.size < sr // 4:
        return 0.0
    f0, voiced, _ = librosa.pyin(mono, fmin=60, fmax=500, sr=sr, frame_length=2048)
    voiced_f0 = f0[voiced & ~np.isnan(f0)] if f0 is not None else np.array([])
    return float(np.median(voiced_f0)) if voiced_f0.size else 0.0


# ---------------------------------------------------------------- loudness (ITU-R BS.1770, simplified gating)

def biquad(kind: str, fc: float, sr: int, q: float = 0.7071, gain_db: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """RBJ audio-EQ-cookbook biquad coefficients (b, a)."""
    fc = min(fc, sr * 0.45)
    a_gain = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * fc / sr
    alpha = np.sin(w0) / (2 * q)
    cos = np.cos(w0)
    if kind == "highpass":
        b = [(1 + cos) / 2, -(1 + cos), (1 + cos) / 2]
        a = [1 + alpha, -2 * cos, 1 - alpha]
    elif kind == "lowpass":
        b = [(1 - cos) / 2, 1 - cos, (1 - cos) / 2]
        a = [1 + alpha, -2 * cos, 1 - alpha]
    elif kind == "peaking":
        b = [1 + alpha * a_gain, -2 * cos, 1 - alpha * a_gain]
        a = [1 + alpha / a_gain, -2 * cos, 1 - alpha / a_gain]
    elif kind == "highshelf":
        sq = 2 * np.sqrt(a_gain) * alpha
        b = [
            a_gain * ((a_gain + 1) + (a_gain - 1) * cos + sq),
            -2 * a_gain * ((a_gain - 1) + (a_gain + 1) * cos),
            a_gain * ((a_gain + 1) + (a_gain - 1) * cos - sq),
        ]
        a = [
            (a_gain + 1) - (a_gain - 1) * cos + sq,
            2 * ((a_gain - 1) - (a_gain + 1) * cos),
            (a_gain + 1) - (a_gain - 1) * cos - sq,
        ]
    else:
        raise ValueError(f"Unknown filter kind: {kind}")
    b_arr, a_arr = np.array(b, dtype=np.float64), np.array(a, dtype=np.float64)
    return b_arr / a_arr[0], a_arr / a_arr[0]


def apply_biquad(y: np.ndarray, coeffs: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    b, a = coeffs
    return signal.lfilter(b, a, y, axis=0).astype(np.float32)


def loudness_lufs(y: np.ndarray, sr: int) -> float:
    """Integrated loudness with K-weighting and absolute/relative gating."""
    mono = to_mono(y).astype(np.float64)
    if mono.size < int(0.4 * sr):
        return rms_db(mono) - 0.691
    weighted = signal.lfilter(*biquad("highshelf", 1681.97, sr, q=0.7072, gain_db=4.0), mono)
    weighted = signal.lfilter(*biquad("highpass", 38.14, sr, q=0.5003), weighted)
    block, step = int(0.4 * sr), int(0.1 * sr)
    energies = np.array(
        [np.mean(weighted[i : i + block] ** 2) for i in range(0, len(weighted) - block + 1, step)]
    )
    lk = -0.691 + 10 * np.log10(energies + EPS)
    gated = energies[lk > -70]
    if gated.size == 0:
        return -70.0
    relative = -0.691 + 10 * np.log10(np.mean(gated) + EPS) - 10
    gated = energies[(lk > -70) & (lk > relative)]
    return float(-0.691 + 10 * np.log10(np.mean(gated) + EPS)) if gated.size else -70.0


# ---------------------------------------------------------------- basic transforms

def resample(y: np.ndarray, sr_from: int, sr_to: int) -> np.ndarray:
    if sr_from == sr_to or y.size == 0:
        return y
    from math import gcd

    g = gcd(int(sr_from), int(sr_to))
    return signal.resample_poly(y, sr_to // g, sr_from // g, axis=0).astype(np.float32)


def gain(y: np.ndarray, db: float) -> np.ndarray:
    return (y * (10 ** (db / 20))).astype(np.float32)


def fade(y: np.ndarray, sr: int, fade_in_s: float = 0.0, fade_out_s: float = 0.0) -> np.ndarray:
    out = y.copy()
    n_in = min(len(out), int(fade_in_s * sr))
    n_out = min(len(out), int(fade_out_s * sr))
    shape = (-1, 1) if out.ndim > 1 else (-1,)
    if n_in:
        out[:n_in] *= np.linspace(0, 1, n_in, dtype=np.float32).reshape(shape)
    if n_out:
        out[-n_out:] *= np.linspace(1, 0, n_out, dtype=np.float32).reshape(shape)
    return out


def silence(seconds: float, sr: int, channels: int = 1) -> np.ndarray:
    n = max(0, int(seconds * sr))
    return np.zeros((n, channels) if channels > 1 else n, dtype=np.float32)


def concat(parts: list[np.ndarray]) -> np.ndarray:
    parts = [p for p in parts if p.size]
    return np.concatenate(parts, axis=0).astype(np.float32) if parts else np.zeros(0, dtype=np.float32)


def trim_silence(y: np.ndarray, sr: int, threshold_db: float, pad_ms: float = 80.0) -> np.ndarray:
    levels = frame_rms_db(y, sr)
    frame = max(1, int(sr * 0.02))
    voiced = np.where(levels > threshold_db)[0]
    if voiced.size == 0:
        return y
    pad = int(sr * pad_ms / 1000)
    start = max(0, voiced[0] * frame - pad)
    end = min(len(y), (voiced[-1] + 1) * frame + pad)
    return y[start:end]
