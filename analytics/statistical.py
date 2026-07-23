"""Normalization, standardization, and correlation calculations.

Implements z-score, min-max, and robust normalizations, Pearson
correlation, correlation / covariance matrices, and a full
descriptive-statistics summary — all using vectorized NumPy.
"""

import numpy as np
from numpy.typing import ArrayLike

from core.logging import get_logger

logger = get_logger(__name__)


class StatisticalAnalyzer:
    """Production statistical analysis engine."""

    @staticmethod
    def z_score_normalize(values: ArrayLike) -> np.ndarray:
        """Standard z-score normalization.

        Formula: z = (x - mean) / std
        Returns zeros when std == 0 (constant array).

        Args:
            values: 1-D numeric array.

        Returns:
            1-D ndarray of z-score normalized values.
        """
        arr = np.asarray(values, dtype=np.float64)
        mean = arr.mean()
        std = arr.std()
        if std == 0:
            logger.warning("Std is 0; returning zeros for z-score.")
            return np.zeros_like(arr)
        return (arr - mean) / std

    @staticmethod
    def min_max_normalize(
        values: ArrayLike,
        feature_range: tuple[float, float] = (0.0, 1.0),
    ) -> np.ndarray:
        """Min-max normalization to a target feature range.

        Formula:
            scaled = (x - x_min) / (x_max - x_min)
            result = scaled * (new_max - new_min) + new_min

        Args:
            values: 1-D numeric array.
            feature_range: Target (min, max) range.

        Returns:
            1-D ndarray scaled to feature_range.
        """
        arr = np.asarray(values, dtype=np.float64)
        x_min, x_max = arr.min(), arr.max()
        span = x_max - x_min
        if span == 0:
            logger.warning("Constant array; returning midpoint of range.")
            mid = (feature_range[0] + feature_range[1]) / 2
            return np.full_like(arr, mid)
        new_min, new_max = feature_range
        scaled = (arr - x_min) / span
        return scaled * (new_max - new_min) + new_min

    @staticmethod
    def robust_normalize(values: ArrayLike) -> np.ndarray:
        """Robust normalization using median and IQR.

        Formula: (x - median) / IQR
        Resistant to outlier influence.

        Args:
            values: 1-D numeric array.

        Returns:
            1-D ndarray of robustly normalized values.
        """
        arr = np.asarray(values, dtype=np.float64)
        median = np.median(arr)
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1
        if iqr == 0:
            logger.warning("IQR is 0; returning zeros for robust norm.")
            return np.zeros_like(arr)
        return (arr - median) / iqr

    @staticmethod
    def pearson_correlation(
        x: ArrayLike,
        y: ArrayLike,
    ) -> float:
        """Compute Pearson correlation coefficient.

        Args:
            x: 1-D numeric array.
            y: 1-D numeric array of same length.

        Returns:
            Pearson r as a float in [-1, 1].
        """
        return float(
            np.corrcoef(
                np.asarray(x, dtype=np.float64),
                np.asarray(y, dtype=np.float64),
            )[0, 1]
        )

    @staticmethod
    def correlation_matrix(
        data_dict: dict[str, ArrayLike],
    ) -> tuple[np.ndarray, list[str]]:
        """Compute pairwise Pearson correlation matrix.

        Args:
            data_dict: Mapping of column_name -> 1-D array.

        Returns:
            Tuple of (correlation_matrix, column_names).
        """
        names = list(data_dict.keys())
        stacked = np.array([np.asarray(v, dtype=np.float64) for v in data_dict.values()])
        corr = np.corrcoef(stacked)
        return corr, names

    @staticmethod
    def covariance_matrix(
        data_dict: dict[str, ArrayLike],
    ) -> tuple[np.ndarray, list[str]]:
        """Compute pairwise covariance matrix.

        Args:
            data_dict: Mapping of column_name -> 1-D array.

        Returns:
            Tuple of (covariance_matrix, column_names).
        """
        names = list(data_dict.keys())
        stacked = np.array([np.asarray(v, dtype=np.float64) for v in data_dict.values()])
        cov = np.cov(stacked)
        return cov, names

    @staticmethod
    def descriptive_statistics(
        values: ArrayLike,
    ) -> dict[str, float]:
        """Compute comprehensive descriptive statistics.

        Returns dict with: mean, median, std, var, min, max,
        range, q1, q3, iqr, skewness, kurtosis.

        Skewness and kurtosis are computed manually with NumPy
        vectorized operations (Fisher definition).

        Args:
            values: 1-D numeric array.

        Returns:
            Dictionary of named statistics.
        """
        arr = np.asarray(values, dtype=np.float64)
        n = len(arr)
        mean = float(arr.mean())
        std = float(arr.std(ddof=0))
        q1 = float(np.percentile(arr, 25))
        q3 = float(np.percentile(arr, 75))

        # Skewness (Fisher): E[(x-mu)^3] / std^3
        if std > 0 and n > 2:
            diff = arr - mean
            skewness = float(np.mean(diff**3) / std**3)
        else:
            skewness = 0.0

        # Kurtosis (excess / Fisher): E[(x-mu)^4]/std^4 - 3
        m4 = float(np.mean((arr - mean) ** 4) / std**4 - 3.0)
        kurtosis = m4 if std > 0 and n > 3 else 0.0

        stats: dict[str, float] = {
            "mean": mean,
            "median": float(np.median(arr)),
            "std": std,
            "var": float(arr.var(ddof=0)),
            "min": float(arr.min()),
            "max": float(arr.max()),
            "range": float(arr.max() - arr.min()),
            "q1": q1,
            "q3": q3,
            "iqr": q3 - q1,
            "skewness": skewness,
            "kurtosis": kurtosis,
        }
        return stats
