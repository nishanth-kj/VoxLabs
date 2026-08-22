import logging
import sys
import os
from pathlib import Path
from datetime import datetime

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

    return logger

# Default logger for the entire project
logger = setup_logger("VoxLabs")
