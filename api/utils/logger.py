import logging
import sys
import os
from collections import deque
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# Environment-based configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))

# Configure logging levels
LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
current_level = LEVELS.get(LOG_LEVEL, logging.INFO)

# Structured format: timestamp - name - level - message
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

_LOG_BUFFER: deque[dict[str, Any]] = deque(maxlen=500)


class MemoryLogHandler(logging.Handler):
    """Keep recent log records in memory for the Studio logs panel."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            _LOG_BUFFER.append({
                "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
                "level": record.levelname.lower(),
                "logger": record.name,
                "message": record.getMessage(),
            })
        except Exception:
            self.handleError(record)


def get_recent_logs(limit: int = 200) -> list[dict[str, Any]]:
    items = list(_LOG_BUFFER)
    if limit > 0:
        items = items[-limit:]
    return items


def setup_logger(name: str):
    """
    Setup a logger with the given name.
    """
    logger = logging.getLogger(name)
    logger.setLevel(current_level)

    # Avoid adding multiple handlers
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)

        # File handler
        if LOG_TO_FILE:
            LOG_DIR.mkdir(exist_ok=True)
            log_file = LOG_DIR / "voxlabs.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
            logger.addHandler(file_handler)

        logger.addHandler(MemoryLogHandler())

    return logger

# Default logger for the entire project
logger = setup_logger("VoxLabs")
