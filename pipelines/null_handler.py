"""Per-column null handling and imputation pipeline module.

Architectural Rule:
------------------
Never apply blanket `fillna(0)` or `dropna()` across an entire dataset.
Each column must follow an explicit, documented strategy:
1. `drop`: Drop rows where critical identifiers or target metrics are missing.
2. `impute_median` / `impute_mean` / `impute_mode`: Impute missing values using statistics.
3. `fill_value`: Replace nulls with an explicit default (e.g. 0.0 for discount).
4. `flag`: Add a binary indicator column `col_is_missing` and impute value.
"""

from typing import Any, Literal

import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)


class NullHandler:
    """Production null-handling engine executing explicit column strategies."""

    def __init__(self, strategies: dict[str, dict[str, Any]]) -> None:
        """Initialize with a dictionary mapping column names to strategy specs."""
        self.strategies = strategies

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies configured per-column null strategies to input DataFrame.

        Args:
            df: Input DataFrame.

        Returns:
            Processed Pandas DataFrame with resolved missing values.
        """
        processed_df = df.copy()
        logger.info(
            "Executing explicit null-handling strategies across %d columns...", len(df.columns)
        )

        for col, spec in self.strategies.items():
            if col not in processed_df.columns:
                continue

            null_count = int(processed_df[col].isna().sum())
            if null_count == 0:
                continue

            action: Literal[
                "drop", "impute_median", "impute_mean", "impute_mode", "fill_value", "flag"
            ] = spec.get("action", "drop")

            logger.info(
                "Column '%s' has %d nulls -> Applying strategy '%s'", col, null_count, action
            )

            if action == "drop":
                processed_df = processed_df.dropna(subset=[col])
            elif action == "fill_value":
                fill_val = spec.get("value", 0)
                processed_df[col] = processed_df[col].fillna(fill_val)
            elif action == "impute_median":
                median_val = processed_df[col].median()
                processed_df[col] = processed_df[col].fillna(median_val)
            elif action == "impute_mean":
                mean_val = processed_df[col].mean()
                processed_df[col] = processed_df[col].fillna(mean_val)
            elif action == "impute_mode":
                mode_val = processed_df[col].mode()[0]
                processed_df[col] = processed_df[col].fillna(mode_val)
            elif action == "flag":
                processed_df[f"{col}_is_missing"] = processed_df[col].isna().astype(int)
                fill_val = spec.get("value", 0)
                processed_df[col] = processed_df[col].fillna(fill_val)
            else:
                raise ValueError(f"Unknown null handling strategy '{action}' for column '{col}'")

        logger.info("Null-handling pass completed (remaining rows: %d).", len(processed_df))
        return processed_df
