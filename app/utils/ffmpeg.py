"""Thin wrappers around the FFmpeg / FFprobe executables (optional dependency)."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np

from app.exceptions import AudioError
from app.utils.logger import logger

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def executable(name: str = "ffmpeg") -> str | None:
    return shutil.which(name)


def available() -> bool:
    return executable("ffmpeg") is not None


def version() -> str | None:
    exe = executable()
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=10, creationflags=_NO_WINDOW)
        return out.stdout.splitlines()[0] if out.stdout else None
    except Exception:
        return None


def run(args: list[str], timeout: float = 600) -> subprocess.CompletedProcess:
    exe = executable()
    if not exe:
        raise AudioError("FFmpeg is not installed or not on PATH")
    logger.debug(f"FFmpeg {' '.join(args[:2])} ...")
    result = subprocess.run(
        [exe, "-hide_banner", "-loglevel", "error", "-y", *args],
        capture_output=True,
        timeout=timeout,
        creationflags=_NO_WINDOW,
    )
    if result.returncode != 0:
        detail = result.stderr.decode(errors="ignore").strip()[:300]
        logger.error(f"FFmpeg exited with {result.returncode}: {detail}")
        raise AudioError(f"FFmpeg failed: {detail}")
    return result


def convert(src: str | Path, dst: str | Path, metadata: dict | None = None, sample_rate: int | None = None) -> Path:
    args = ["-i", str(src)]
    for key, value in (metadata or {}).items():
        args += ["-metadata", f"{key}={value}"]
    if sample_rate:
        args += ["-ar", str(sample_rate)]
    args.append(str(dst))
    run(args)
    return Path(dst)


def decode(path: str | Path, sample_rate: int | None = None) -> tuple[np.ndarray, int]:
    """Decode any FFmpeg-supported file to float32 mono PCM."""
    sr = sample_rate or int(probe(path).get("sample_rate") or 44100)
    result = run(["-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(sr), "pipe:1"])
    return np.frombuffer(result.stdout, dtype=np.float32).copy(), sr


def probe(path: str | Path) -> dict:
    exe = executable("ffprobe")
    if not exe:
        raise AudioError("FFprobe is not installed or not on PATH")
    out = subprocess.run(
        [exe, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
        capture_output=True,
        text=True,
        timeout=60,
        creationflags=_NO_WINDOW,
    )
    if out.returncode != 0:
        raise AudioError(f"Cannot probe {Path(path).name}")
    data = json.loads(out.stdout or "{}")
    stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    fmt = data.get("format", {})
    return {
        "duration": float(fmt.get("duration") or stream.get("duration") or 0),
        "sample_rate": int(stream.get("sample_rate") or 0),
        "channels": int(stream.get("channels") or 0),
        "format": Path(path).suffix.lower().lstrip("."),
        "codec": stream.get("codec_name"),
    }
