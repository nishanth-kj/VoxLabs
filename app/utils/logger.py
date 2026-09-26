"""Centralized logging. Never log audio content, file bytes or credentials.

Every record carries a `source`: who started the work that logged it.

    ui      the desktop app            api     a REST API request
    mcp     an MCP tool call           system  startup, shutdown, timers

Entry points set it with `log_source(...)`; background jobs and UI worker threads
inherit it from the caller, so a job started over the API logs as "api".
"""

import itertools
import logging
import os
import sys
import threading
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(source)s] %(message)s"
LOG_SOURCES = ("ui", "api", "mcp", "system")
LOG_BUFFER_SIZE = 2000

_SOURCE: ContextVar[str] = ContextVar("voxlabs_log_source", default="system")
_LOG_BUFFER: deque[dict[str, Any]] = deque(maxlen=LOG_BUFFER_SIZE)
_LOG_LOCK = threading.Lock()  # records arrive from worker threads
_SEQUENCE = itertools.count(1)


def set_log_source(source: str) -> None:
    """Tag everything the current thread logs from now on (the desktop's UI thread uses "ui")."""
    _SOURCE.set(source)


@contextmanager
def log_source(source: str) -> Iterator[None]:
    """Tag what is logged inside the block, e.g. one API request or one MCP tool call."""
    token = _SOURCE.set(source)
    try:
        yield
    finally:
        _SOURCE.reset(token)


class _SourceFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "source"):
            record.source = _SOURCE.get()
        return True


class MemoryLogHandler(logging.Handler):
    """Keeps recent records in memory for the desktop Logs panel.

    Each record has a growing `seq`, so a viewer can ask only for what is new.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = {
                "seq": next(_SEQUENCE),
                "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
                "level": record.levelname.lower(),
                "source": getattr(record, "source", "system"),
                "message": record.getMessage(),
            }
            with _LOG_LOCK:
                _LOG_BUFFER.append(entry)
        except Exception:
            self.handleError(record)


def get_recent_logs(limit: int = 200, after: int = 0) -> list[dict[str, Any]]:
    """The newest `limit` records, optionally only those with `seq` greater than `after`."""
    with _LOG_LOCK:
        items = [entry for entry in _LOG_BUFFER if entry["seq"] > after] if after else list(_LOG_BUFFER)
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
    handler.addFilter(_SourceFilter())
    logger.addHandler(handler)


def _setup() -> logging.Logger:
    log = logging.getLogger("voxlabs")
    log.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    if not log.handlers:
        console = logging.StreamHandler(sys.stderr)  # stdout is reserved for the MCP stdio transport
        console.setFormatter(logging.Formatter(LOG_FORMAT))
        memory = MemoryLogHandler()
        for handler in (console, memory):
            handler.addFilter(_SourceFilter())
            log.addHandler(handler)
    log.propagate = False
    return log


logger = _setup()
