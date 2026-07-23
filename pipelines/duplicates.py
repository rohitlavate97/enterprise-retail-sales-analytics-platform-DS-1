"""Duplicate detection and deduplication pipeline module.

Identifies exact row duplicates and primary key collisions, producing deduplicated datasets
and quarantine summaries for data auditing.
"""

from typing import Literal

import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)


class DuplicateDetector:
    """Production duplicate detector and deduplicator."""

    @staticmethod
    def deduplicate(
        df: pd.DataFrame,
        subset: list[str] | None = None,
        keep: Literal["first", "last", False] = "first",
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Detects and removes duplicate records from DataFrame.

        Args:
            df: Input DataFrame.
            subset: List of column names to check for duplicate uniqueness (e.g. ['order_id']).
            keep: 'first', 'last', or False (quarantine all copies).

        Returns:
            Tuple of (deduplicated_df, duplicates_df).
        """
        logger.info("Running duplicate detection on subset=%s...", subset)

        num_initial = len(df)
        duplicates_mask = df.duplicated(subset=subset, keep=keep)
        duplicates_df = df[duplicates_mask].copy()

        if keep is False:
            clean_df = df[~duplicates_mask].copy()
        else:
            clean_df = df.drop_duplicates(subset=subset, keep=keep).copy()

        num_removed = num_initial - len(clean_df)
        logger.info(
            "Deduplication complete: %d initial, %d duplicates, %d clean rows retained.",
            num_initial,
            num_removed,
            len(clean_df),
        )
        return clean_df, duplicates_df
