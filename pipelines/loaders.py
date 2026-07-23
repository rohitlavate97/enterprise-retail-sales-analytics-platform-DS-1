"""Data loading module supporting CSV and Parquet file formats.

Architectural Rationale:
-----------------------
1. CSV (Comma-Separated Values):
   - Best used as a universal human-readable interchange format.
   - Disadvantages: Text-based parsing overhead, lack of embedded data type metadata,
     uncompressed disk storage, and row-oriented storage layout which forces full file scans
     even when selecting a single column.

2. Apache Parquet:
   - Enterprise standard for columnar analytical data storage.
   - Advantages: Binary format with embedded schema headers, Snappy compression, dictionary
     encoding, and columnar layout allowing projection pushdown (reading only required columns)
     and predicate pushdown (filtering at file-scan level). Yields up to 10x faster I/O speeds
     and 70-90% disk space reduction compared to CSV.
"""

from pathlib import Path
from typing import Literal

import pandas as pd
import polars as pl

from core.logging import get_logger

logger = get_logger(__name__)


class DataLoader:
    """Production DataLoader executing CSV and Parquet read operations."""

    @staticmethod
    def load_pandas(
        file_path: str | Path,
        columns: list[str] | None = None,
        file_format: Literal["csv", "parquet", "auto"] = "auto",
    ) -> pd.DataFrame:
        """Loads a dataset into a Pandas DataFrame.

        Args:
            file_path: Absolute or relative file path to load.
            columns: Optional subset of columns to project.
            file_format: Explicit format ('csv' or 'parquet') or auto-detect from extension.

        Returns:
            Pandas DataFrame.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Source file not found at {path}")

        fmt = path.suffix.lstrip(".").lower() if file_format == "auto" else file_format.lower()

        logger.info("Loading file via Pandas: %s (format=%s)...", path.name, fmt)

        if fmt == "parquet":
            df = pd.read_parquet(path, columns=columns)
        elif fmt == "csv":
            df = pd.read_csv(path, usecols=columns)
        else:
            raise ValueError(f"Unsupported file format: {fmt}")

        logger.info("Successfully loaded %s via Pandas (shape: %s).", path.name, df.shape)
        return df

    @staticmethod
    def load_polars(
        file_path: str | Path,
        columns: list[str] | None = None,
        file_format: Literal["csv", "parquet", "auto"] = "auto",
    ) -> pl.DataFrame:
        """Loads a dataset into a Polars DataFrame.

        Args:
            file_path: Absolute or relative file path to load.
            columns: Optional subset of columns to project.
            file_format: Explicit format ('csv' or 'parquet') or auto-detect from extension.

        Returns:
            Polars DataFrame.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Source file not found at {path}")

        fmt = path.suffix.lstrip(".").lower() if file_format == "auto" else file_format.lower()

        logger.info("Loading file via Polars: %s (format=%s)...", path.name, fmt)

        if fmt == "parquet":
            df = pl.read_parquet(path, columns=columns)
        elif fmt == "csv":
            df = pl.read_csv(path, columns=columns)
        else:
            raise ValueError(f"Unsupported file format: {fmt}")

        logger.info("Successfully loaded %s via Polars (shape: %s).", path.name, df.shape)
        return df
