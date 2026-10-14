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


def probe_media(path: str | Path) -> dict:
    """Probe media file for both video and audio streams."""
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
        raise AudioError(f"Cannot probe media {Path(path).name}")
    data = json.loads(out.stdout or "{}")
    streams = data.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = data.get("format", {})

    # Calculate FPS safely from rational like '30/1' or '24000/1001'
    fps = 0.0
    if v_stream and (r_fps := v_stream.get("r_frame_rate")):
        try:
            num, denom = r_fps.split("/")
            fps = round(float(num) / float(denom), 2) if float(denom) > 0 else 0.0
        except (ValueError, ZeroDivisionError):
            fps = 0.0

    duration = float(
        fmt.get("duration")
        or (v_stream.get("duration") if v_stream else None)
        or (a_stream.get("duration") if a_stream else None)
        or 0.0
    )

    return {
        "has_video": v_stream is not None,
        "has_audio": a_stream is not None,
        "duration": duration,
        "format": Path(path).suffix.lower().lstrip("."),
        "video_codec": v_stream.get("codec_name") if v_stream else None,
        "width": int(v_stream.get("width") or 0) if v_stream else None,
        "height": int(v_stream.get("height") or 0) if v_stream else None,
        "fps": fps if v_stream else None,
        "audio_codec": a_stream.get("codec_name") if a_stream else None,
        "sample_rate": int(a_stream.get("sample_rate") or 0) if a_stream else None,
        "channels": int(a_stream.get("channels") or 0) if a_stream else None,
    }


def extract_audio(src: str | Path, dst: str | Path, sample_rate: int = 44100) -> Path:
    """Extract audio stream from a video or audio container safely to WAV."""
    args = ["-i", str(src), "-vn", "-ac", "1", "-ar", str(sample_rate), "-c:a", "pcm_s16le", str(dst)]
    run(args)
    return Path(dst)


def remux_video(video_path: str | Path, audio_path: str | Path, dst_path: str | Path,
                video_mode: str = "copy", crf: int = 20, audio_bitrate: str = "192k") -> Path:
    """Remux new dubbed audio into a video container, preserving lossless video stream when mode is 'copy'."""
    args = ["-i", str(video_path), "-i", str(audio_path)]
    if video_mode == "copy":
        args += ["-c:v", "copy"]
    else:
        args += ["-c:v", "libx264", "-crf", str(crf), "-preset", "fast"]
    args += ["-c:a", "aac", "-b:a", str(audio_bitrate), "-map", "0:v:0", "-map", "1:a:0", "-shortest", str(dst_path)]
    run(args)
    return Path(dst_path)
