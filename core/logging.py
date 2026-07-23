"""Structured logging setup module.

Provides a unified logger factory producing consistent console and file logger instances
with JSON or formatted text outputs according to system settings.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

from config.settings import get_settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging output."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Factory function to retrieve a configured Logger instance.

    Args:
        name: Name of the logger (typically __name__ of calling module).

    Returns:
        Configured logging.Logger object.
    """
    settings = get_settings()
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if already configured
    if logger.hasHandlers():
        return logger

    log_level = getattr(logging, settings.logging.level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if settings.logging.format == "json":
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    log_file_path = Path(settings.logging.log_file)
    try:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as exc:
        # Fallback to console logging if file system permission issue
        logger.warning("Could not setup file logger at %s: %s", log_file_path, exc)

    return logger
