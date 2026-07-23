"""Numeric downcasting and categorical dtype memory optimization pipeline stage.

Reduces DataFrame RAM footprint by downcasting 64-bit numeric types to minimal width
integral/float types and converting low-cardinality string columns to 'category' dtypes.
"""

from typing import Any

import numpy as np
import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)


class MemoryOptimizer:
    """Production memory optimization pass for Pandas DataFrames."""

    @staticmethod
    def optimize(df: pd.DataFrame, categorical_threshold: float = 0.50) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Downcasts numeric columns and converts low-cardinality strings to categorical dtypes.

        Args:
            df: Input DataFrame to optimize.
            categorical_threshold: Ratio of unique string values below which a column is converted to category.

        Returns:
            Tuple of (optimized_df, memory_report_dict).
        """
        initial_mem_bytes = df.memory_usage(deep=True).sum()
        initial_mem_mb = initial_mem_bytes / (1024 * 1024)

        logger.info(
            "Starting memory optimization pass on DataFrame (initial RAM: %.2f MB, %d rows)...",
            initial_mem_mb,
            len(df),
        )

        optimized_df = df.copy()
        num_rows = len(df)

        for col in optimized_df.columns:
            col_type = optimized_df[col].dtype

            # 1. Downcast integer columns
            if np.issubdtype(col_type, np.integer):
                c_min = optimized_df[col].min()
                c_max = optimized_df[col].max()
                if c_min >= 0:
                    if c_max < 255:
                        optimized_df[col] = optimized_df[col].astype(np.uint8)
                    elif c_max < 65535:
                        optimized_df[col] = optimized_df[col].astype(np.uint16)
                    elif c_max < 4294967295:
                        optimized_df[col] = optimized_df[col].astype(np.uint32)
                else:
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        optimized_df[col] = optimized_df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        optimized_df[col] = optimized_df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        optimized_df[col] = optimized_df[col].astype(np.int32)

            # 2. Downcast float columns (float64 -> float32)
            elif np.issubdtype(col_type, np.floating):
                optimized_df[col] = optimized_df[col].astype(np.float32)

            # 3. Convert low-cardinality object strings to categorical
            elif col_type == object or isinstance(col_type, pd.StringDtype):
                num_unique = optimized_df[col].nunique(dropna=True)
                if num_rows > 0 and (num_unique / num_rows) < categorical_threshold:
                    optimized_df[col] = optimized_df[col].astype("category")

        final_mem_bytes = optimized_df.memory_usage(deep=True).sum()
        final_mem_mb = final_mem_bytes / (1024 * 1024)
        savings_mb = initial_mem_mb - final_mem_mb
        reduction_pct = (savings_mb / initial_mem_mb) * 100 if initial_mem_mb > 0 else 0.0

        report: dict[str, Any] = {
            "initial_memory_mb": round(initial_mem_mb, 2),
            "optimized_memory_mb": round(final_mem_mb, 2),
            "savings_mb": round(savings_mb, 2),
            "reduction_percent": round(reduction_pct, 2),
        }

        logger.info(
            "Memory optimization complete: %.2f MB -> %.2f MB (Saved %.2f MB / %.1f%% reduction).",
            initial_mem_mb,
            final_mem_mb,
            savings_mb,
            reduction_pct,
        )
        return optimized_df, report
