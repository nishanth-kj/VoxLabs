"""Application directories, safe file naming and path helpers."""

import os
import re
import shutil
import sys
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_SUBDIRS = ("database", "voices", "audio", "models", "jobs", "cache", "exports", "logs")


def default_data_dir() -> Path:
    """`data/` next to the code when run from source. A built app (PyInstaller) keeps data in the
    user's app-data folder instead: its own folder can be read-only (Program Files, a signed .app)
    and is replaced on every update."""
    if not getattr(sys, "frozen", False):
        return PROJECT_ROOT / "data"
    if sys.platform == "win32":
        base = Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.getenv("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "VoxLabs"


def data_dir() -> Path:
    """Root of all VoxLabs data. Override with VOXLABS_DATA_DIR."""
    root = Path(os.getenv("VOXLABS_DATA_DIR") or default_data_dir())
    root.mkdir(parents=True, exist_ok=True)
    return root


def subdir(name: str, *parts: str | int) -> Path:
    path = data_dir() / name
    for part in parts:
        path = path / str(part)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_data_dirs() -> None:
    for name in DATA_SUBDIRS:
        subdir(name)


_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_name(name: str, max_length: int = 60) -> str:
    cleaned = _UNSAFE.sub("_", name).strip("._") or "file"
    return cleaned[:max_length]


def unique_path(directory: Path, stem: str, ext: str) -> Path:
    """A new, non-existing path like <dir>/<stem>_<short uuid>.<ext>."""
    directory.mkdir(parents=True, exist_ok=True)
    ext = ext.lstrip(".")
    return directory / f"{safe_name(stem)}_{uuid.uuid4().hex[:10]}.{ext}"


def extension(path: str | Path) -> str:
    return Path(path).suffix.lower().lstrip(".")


def file_size(path: str | Path) -> int:
    try:
        return Path(path).stat().st_size
    except OSError:
        return 0


def remove_file(path: str | Path | None) -> None:
    if path:
        Path(path).unlink(missing_ok=True)


def remove_tree(path: str | Path | None) -> None:
    if path and Path(path).exists():
        shutil.rmtree(path, ignore_errors=True)


def copy_file(src: str | Path, dst: str | Path) -> Path:
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def save_upload(upload: UploadFile) -> Path:
    """Stream an uploaded file into data/cache/uploads. Callers remove it when done (services keep copies)."""
    suffix = Path(upload.filename or "").suffix.lower()
    with NamedTemporaryFile(delete=False, suffix=suffix, dir=subdir("cache", "uploads")) as handle:
        shutil.copyfileobj(upload.file, handle)
    return Path(handle.name)
