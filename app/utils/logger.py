"""Centralized logging. Never log audio content, file bytes or credentials."""

import logging
import os
import sys
from collections import deque
from datetime import datetime, timezone
from typing import Any

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

_LOG_BUFFER: deque[dict[str, Any]] = deque(maxlen=500)


class MemoryLogHandler(logging.Handler):
    """Keeps recent records in memory for the Settings > Logs view."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            _LOG_BUFFER.append(
                {
                    "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
                    "level": record.levelname.lower(),
                    "message": record.getMessage(),
                }
            )
        except Exception:
            self.handleError(record)


def get_recent_logs(limit: int = 200) -> list[dict[str, Any]]:
    items = list(_LOG_BUFFER)
    return items[-limit:] if limit > 0 else items


def set_level(level: str) -> None:
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))


def enable_file_logging() -> None:
    """Attach a file handler under data/logs (called once at app startup)."""
    from app.utils.files import subdir

    if any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        return
    handler = logging.FileHandler(subdir("logs") / "voxlabs.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)


def _setup() -> logging.Logger:
    log = logging.getLogger("voxlabs")
    log.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    if not log.handlers:
        console = logging.StreamHandler(sys.stderr)  # stdout is reserved for the MCP stdio transport
        console.setFormatter(logging.Formatter(LOG_FORMAT))
        log.addHandler(console)
        log.addHandler(MemoryLogHandler())
    log.propagate = False
    return log


logger = _setup()
