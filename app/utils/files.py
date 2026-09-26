"""Application directories, safe file naming and path helpers."""

import os
import re
import shutil
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_SUBDIRS = ("database", "voices", "audio", "projects", "models", "jobs", "cache", "exports", "logs")


def data_dir() -> Path:
    """Root of all VoxLabs data. Override with VOXLABS_DATA_DIR."""
    root = Path(os.getenv("VOXLABS_DATA_DIR") or PROJECT_ROOT / "data")
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
