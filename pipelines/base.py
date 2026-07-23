"""Base pipeline abstractions and structured exception handlers.

Provides abstract base classes for ETL pipeline stages and context managers for structured logging
and graceful exception propagation.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
import time
from typing import Any, Generator

from core.logging import get_logger

logger = get_logger(__name__)


class PipelineStage(ABC):
    """Abstract base class for modular data pipeline stages."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """Executes stage transformation logic."""
        pass


@contextmanager
def stage_execution_context(stage_name: str) -> Generator[None, None, None]:
    """Context manager for timing, logging, and handling errors in pipeline stages."""
    logger.info(">>> Starting Pipeline Stage: [%s]", stage_name)
    start_time = time.perf_counter()
    try:
        yield
        elapsed = time.perf_counter() - start_time
        logger.info("<<< Completed Pipeline Stage: [%s] in %.3f seconds.", stage_name, elapsed)
    except Exception as exc:
        elapsed = time.perf_counter() - start_time
        logger.error(
            "!!! FAILED Pipeline Stage: [%s] after %.3f seconds. Error: %s",
            stage_name,
            elapsed,
            exc,
            exc_info=True,
        )
        raise RuntimeError(f"Pipeline stage '{stage_name}' failed: {exc}") from exc
