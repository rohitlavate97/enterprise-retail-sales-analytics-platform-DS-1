"""Statistical outlier detection and treatment pipeline module.

Supports Interquartile Range (IQR) and Z-score statistical methods applied per metric,
with configurable treatment strategies (flagging, winsorizing/clipping, or quarantining).
"""

from typing import Literal

import numpy as np
import pandas as pd

from config.settings import get_settings
from core.logging import get_logger

logger = get_logger(__name__)


class OutlierDetector:
    """Production statistical outlier detection engine."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def detect_iqr(
        self,
        df: pd.DataFrame,
        column: str,
        multiplier: float | None = None,
        action: Literal["flag", "clip", "quarantine"] = "flag",
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Detects outliers using Interquartile Range (IQR) bounds.

        Bounds: [Q1 - k * IQR, Q3 + k * IQR]

        Args:
            df: Input DataFrame.
            column: Target numeric column name.
            multiplier: IQR multiplier k (defaults to config multiplier = 1.5).
            action: Treatment action ('flag', 'clip', or 'quarantine').

        Returns:
            Tuple of (processed_df, outlier_boolean_mask).
        """
        k = multiplier if multiplier is not None else self.settings.analytics.outlier_iqr_multiplier
        series = df[column]

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr

        outlier_mask = (series < lower_bound) | (series > upper_bound)
        num_outliers = int(outlier_mask.sum())

        logger.info(
            "IQR Outlier detection on '%s' (k=%.2f): Bounds=[%.2f, %.2f] | Outliers=%d (%.2f%%)",
            column,
            k,
            lower_bound,
            upper_bound,
            num_outliers,
            (num_outliers / len(df)) * 100 if len(df) > 0 else 0.0,
        )

        processed_df = df.copy()

        if action == "flag":
            processed_df[f"{column}_is_outlier"] = outlier_mask.astype(int)
        elif action == "clip":
            processed_df[column] = processed_df[column].clip(lower=lower_bound, upper=upper_bound)
        elif action == "quarantine":
            processed_df = processed_df[~outlier_mask].copy()

        return processed_df, outlier_mask

    def detect_zscore(
        self,
        df: pd.DataFrame,
        column: str,
        threshold: float | None = None,
        action: Literal["flag", "clip", "quarantine"] = "flag",
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Detects outliers using Z-score standardized deviation bounds.

        Bounds: [mean - z * std, mean + z * std]

        Args:
            df: Input DataFrame.
            column: Target numeric column name.
            threshold: Z-score threshold z (defaults to config threshold = 3.0).
            action: Treatment action ('flag', 'clip', or 'quarantine').

        Returns:
            Tuple of (processed_df, outlier_boolean_mask).
        """
        z_thresh = (
            threshold if threshold is not None else self.settings.analytics.outlier_zscore_threshold
        )
        series = df[column]
        mean = series.mean()
        std = series.std()

        if std == 0 or np.isnan(std):
            logger.info("Z-score detection skipped on '%s': zero standard deviation.", column)
            return df.copy(), pd.Series(False, index=df.index)

        z_scores = (series - mean) / std
        outlier_mask = z_scores.abs() > z_thresh
        num_outliers = int(outlier_mask.sum())

        logger.info(
            "Z-score Outlier detection on '%s' (z=%.2f): Outliers=%d (%.2f%%)",
            column,
            z_thresh,
            num_outliers,
            (num_outliers / len(df)) * 100 if len(df) > 0 else 0.0,
        )

        processed_df = df.copy()

        if action == "flag":
            processed_df[f"{column}_is_outlier"] = outlier_mask.astype(int)
        elif action == "clip":
            lower_bound = mean - z_thresh * std
            upper_bound = mean + z_thresh * std
            processed_df[column] = processed_df[column].clip(lower=lower_bound, upper=upper_bound)
        elif action == "quarantine":
            processed_df = processed_df[~outlier_mask].copy()

        return processed_df, outlier_mask
