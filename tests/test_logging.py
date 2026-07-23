"""Unit tests for structured logging module."""

import logging
from pathlib import Path
import tempfile
import json
from core.logging import get_logger, JSONFormatter


def test_get_logger_creation() -> None:
    """Test logger initialization and handler attachment."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"
    assert logger.hasHandlers()


def test_json_formatter() -> None:
    """Test JSONFormatter output structure."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test log message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["logger"] == "test_logger"
    assert data["level"] == "INFO"
    assert data["message"] == "Test log message"
    assert data["lineno"] == 10
    assert "timestamp" in data
