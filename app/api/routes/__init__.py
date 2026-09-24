"""Thin API routers: parse the request class, call a service, wrap the result in ApiResponse."""

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

from app.utils.files import subdir


def save_upload(upload: UploadFile) -> Path:
    """Stream an upload into data/cache/uploads (services copy what they keep)."""
    suffix = Path(upload.filename or "").suffix.lower()
    with NamedTemporaryFile(delete=False, suffix=suffix, dir=subdir("cache", "uploads")) as handle:
        shutil.copyfileobj(upload.file, handle)
    return Path(handle.name)
