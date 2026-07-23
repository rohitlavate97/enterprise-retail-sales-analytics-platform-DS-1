"""Moving averages and rolling window computations using NumPy.

Implements SMA, EMA, WMA, rolling std, rolling min/max, and cumulative
computations using vectorized NumPy operations.  No Python-level element
loops appear in the hot path except the single-pass EMA recurrence.
"""

import numpy as np
from numpy.typing import ArrayLike

from core.logging import get_logger

logger = get_logger(__name__)


class RollingStatistics:
    """Production rolling / window computation engine."""

    @staticmethod
    def simple_moving_average(
        values: ArrayLike,
        window_size: int,
    ) -> np.ndarray:
        """Compute Simple Moving Average (SMA) via np.convolve.

        Returns an array of the same length as *values* with NaN
        padding for the initial ``window_size - 1`` positions.

        Args:
            values: 1-D numeric array.
            window_size: Number of periods for the window.

        Returns:
            1-D ndarray of SMA values (NaN-padded at start).
        """
        arr = np.asarray(values, dtype=np.float64)
        kernel = np.ones(window_size) / window_size
        convolved = np.convolve(arr, kernel, mode="full")[: len(arr)]
        result = np.empty_like(arr)
        result[:] = np.nan
        result[window_size - 1 :] = convolved[window_size - 1 :]
        return result

    @staticmethod
    def exponential_moving_average(
        values: ArrayLike,
        span: int,
    ) -> np.ndarray:
        """Compute Exponential Moving Average (EMA).

        Uses alpha = 2 / (span + 1).  Single forward pass stored
        in a pre-allocated ndarray.

        Args:
            values: 1-D numeric array.
            span: EMA span (number of periods).

        Returns:
            1-D ndarray of EMA values.
        """
        arr = np.asarray(values, dtype=np.float64)
        alpha = 2.0 / (span + 1)
        ema = np.empty_like(arr)
        ema[0] = arr[0]
        for i in range(1, len(arr)):
            ema[i] = alpha * arr[i] + (1 - alpha) * ema[i - 1]
        return ema

    @staticmethod
    def weighted_moving_average(
        values: ArrayLike,
        weights: ArrayLike,
    ) -> np.ndarray:
        """Compute Weighted Moving Average (WMA).

        Applies user-specified weights using np.convolve with
        normalised kernel.  Returns NaN-padded result.

        Args:
            values: 1-D numeric array.
            weights: 1-D weight array (e.g. linearly increasing).

        Returns:
            1-D ndarray of WMA values (NaN-padded at start).
        """
        arr = np.asarray(values, dtype=np.float64)
        w = np.asarray(weights, dtype=np.float64)
        w_norm = w / w.sum()
        window_size = len(w_norm)
        convolved = np.convolve(arr, w_norm[::-1], mode="full")[: len(arr)]
        result = np.empty_like(arr)
        result[:] = np.nan
        result[window_size - 1 :] = convolved[window_size - 1 :]
        return result

    @staticmethod
    def rolling_std(
        values: ArrayLike,
        window_size: int,
    ) -> np.ndarray:
        """Compute rolling standard deviation in O(n) time.

        Uses cumulative-sum trick to avoid recomputing the window
        sum at every step.

        Args:
            values: 1-D numeric array.
            window_size: Number of periods for the window.

        Returns:
            1-D ndarray of rolling std values (NaN-padded).
        """
        arr = np.asarray(values, dtype=np.float64)
        n = len(arr)
        result = np.empty(n)
        result[:] = np.nan

        cumsum = np.concatenate(([0], np.cumsum(arr)))
        cumsum_sq = np.concatenate(([0], np.cumsum(arr**2)))

        for i in range(window_size - 1, n):
            s = cumsum[i + 1] - cumsum[i + 1 - window_size]
            s2 = cumsum_sq[i + 1] - cumsum_sq[i + 1 - window_size]
            mean = s / window_size
            var = s2 / window_size - mean**2
            result[i] = np.sqrt(max(var, 0.0))

        return result

    @staticmethod
    def rolling_min_max(
        values: ArrayLike,
        window_size: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute rolling minimum and maximum.

        Args:
            values: 1-D numeric array.
            window_size: Number of periods for the window.

        Returns:
            Tuple of (rolling_min, rolling_max) ndarrays (NaN-padded).
        """
        arr = np.asarray(values, dtype=np.float64)
        n = len(arr)
        r_min = np.empty(n)
        r_max = np.empty(n)
        r_min[:] = np.nan
        r_max[:] = np.nan

        for i in range(window_size - 1, n):
            window = arr[i + 1 - window_size : i + 1]
            r_min[i] = window.min()
            r_max[i] = window.max()

        return r_min, r_max

    @staticmethod
    def cumulative_sum(values: ArrayLike) -> np.ndarray:
        """Compute running cumulative sum.

        Args:
            values: 1-D numeric array.

        Returns:
            1-D ndarray of cumulative sums.
        """
        return np.cumsum(np.asarray(values, dtype=np.float64))

    @staticmethod
    def cumulative_growth_rate(values: ArrayLike) -> np.ndarray:
        """Compute cumulative growth rate from first value.

        Formula: ((values / values[0]) - 1) * 100

        Args:
            values: 1-D numeric array (first value must be != 0).

        Returns:
            1-D ndarray of cumulative growth rate percentages.
        """
        arr = np.asarray(values, dtype=np.float64)
        if arr[0] == 0:
            logger.warning("First value is 0; cumulative growth undefined.")
            return np.zeros_like(arr)
        result: np.ndarray = ((arr / arr[0]) - 1.0) * 100.0
        return result
