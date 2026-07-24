"""Pandas rolling/window trailing-KPI analytics.

Distinct from ``rolling_stats.py`` (Phase 4), which implements
low-level NumPy array windowing primitives.  This module operates
on **Pandas DataFrames** produced by ``TemporalAnalytics.resample_sales``
to answer trailing-KPI business questions using ``DataFrame.rolling()``,
``DataFrame.expanding()``, and ``DataFrame.pct_change()``.

Business Questions Answered:
- What is the trailing 3-month / 6-month revenue and profit trend?
- What is the rolling average order value over the last N periods?
- How volatile is revenue period-over-period (rolling std)?
- What is the cumulative (expanding) revenue and profit over time?
- What is the period-over-period growth rate in revenue?

Why Pandas ``rolling`` instead of raw NumPy here?
- The input is a time-indexed DataFrame, not a flat array.
- Pandas rolling integrates with DatetimeIndex alignment, NaN
  handling, and multi-column aggregation out of the box — writing
  this by hand in NumPy would be reimplementing Pandas internals
  with no performance gain and worse readability.
"""

import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)


class WindowKPIAnalytics:
    """Trailing-KPI engine using Pandas rolling/expanding windows."""

    @staticmethod
    def trailing_revenue_profit(
        resampled: pd.DataFrame,
        window: int = 3,
    ) -> pd.DataFrame:
        """Compute trailing (rolling) revenue and profit sums.

        Business question: *What is the trailing N-period revenue
        and profit, and how does it compare to the current period?*

        Uses: ``DataFrame.rolling(window).sum()`` on resampled
        time-series data.

        Args:
            resampled: Time-indexed DataFrame from
                ``TemporalAnalytics.resample_sales``.
            window: Number of periods in the trailing window.

        Returns:
            Original DataFrame with added columns:
            ``trailing_{window}p_revenue`` and
            ``trailing_{window}p_profit``.
        """
        logger.info(
            "Computing trailing %d-period revenue & profit...",
            window,
        )
        result = resampled.copy()
        roll = result[["total_revenue", "total_profit"]].rolling(
            window=window, min_periods=1
        )
        result[f"trailing_{window}p_revenue"] = roll[
            "total_revenue"
        ].sum()
        result[f"trailing_{window}p_profit"] = roll[
            "total_profit"
        ].sum()
        return result

    @staticmethod
    def rolling_avg_order_value(
        resampled: pd.DataFrame,
        window: int = 3,
    ) -> pd.DataFrame:
        """Compute rolling average order value (AOV).

        Business question: *What is the smoothed average order
        value over the trailing N periods, filtering out
        single-period spikes?*

        Uses: ``Series.rolling(window).mean()`` on the
        ``avg_order_value`` column.

        Args:
            resampled: Time-indexed DataFrame from
                ``TemporalAnalytics.resample_sales``.
            window: Number of periods in the rolling window.

        Returns:
            Original DataFrame with added column:
            ``rolling_{window}p_aov``.
        """
        logger.info(
            "Computing rolling %d-period AOV...", window
        )
        result = resampled.copy()
        result[f"rolling_{window}p_aov"] = (
            result["avg_order_value"]
            .rolling(window=window, min_periods=1)
            .mean()
        )
        return result

    @staticmethod
    def rolling_revenue_volatility(
        resampled: pd.DataFrame,
        window: int = 3,
    ) -> pd.DataFrame:
        """Compute rolling revenue volatility (standard deviation).

        Business question: *How stable or volatile is revenue
        period-over-period?  Are there high-variance stretches
        that signal operational instability or seasonal swings?*

        Uses: ``Series.rolling(window).std()`` on ``total_revenue``.

        Args:
            resampled: Time-indexed DataFrame from
                ``TemporalAnalytics.resample_sales``.
            window: Number of periods in the rolling window.

        Returns:
            Original DataFrame with added column:
            ``rolling_{window}p_revenue_std``.
        """
        logger.info(
            "Computing rolling %d-period revenue volatility...",
            window,
        )
        result = resampled.copy()
        result[f"rolling_{window}p_revenue_std"] = (
            result["total_revenue"]
            .rolling(window=window, min_periods=2)
            .std()
        )
        return result

    @staticmethod
    def expanding_cumulative(
        resampled: pd.DataFrame,
    ) -> pd.DataFrame:
        """Compute expanding (cumulative) revenue and profit.

        Business question: *What is the cumulative revenue and
        profit to date, and what is the running profit margin?*

        Uses: ``DataFrame.expanding().sum()`` — an expanding window
        includes all rows from the start up to the current row.

        Args:
            resampled: Time-indexed DataFrame from
                ``TemporalAnalytics.resample_sales``.

        Returns:
            Original DataFrame with added columns:
            ``cumulative_revenue``, ``cumulative_profit``, and
            ``cumulative_margin_pct``.
        """
        logger.info("Computing expanding cumulative KPIs...")
        result = resampled.copy()
        exp = result[["total_revenue", "total_profit"]].expanding(
            min_periods=1
        )
        result["cumulative_revenue"] = exp["total_revenue"].sum()
        result["cumulative_profit"] = exp["total_profit"].sum()
        result["cumulative_margin_pct"] = (
            (
                result["cumulative_profit"]
                / result["cumulative_revenue"]
            )
            * 100
        ).fillna(0.0)
        return result

    @staticmethod
    def period_over_period_growth(
        resampled: pd.DataFrame,
    ) -> pd.DataFrame:
        """Compute period-over-period revenue growth rate.

        Business question: *Is revenue accelerating or
        decelerating from one period to the next?*

        Uses: ``Series.pct_change()`` — computes the percentage
        change between the current and prior element.

        Args:
            resampled: Time-indexed DataFrame from
                ``TemporalAnalytics.resample_sales``.

        Returns:
            Original DataFrame with added column:
            ``revenue_growth_pct`` (percentage, not decimal).
        """
        logger.info("Computing period-over-period growth...")
        result = resampled.copy()
        result["revenue_growth_pct"] = (
            result["total_revenue"].pct_change() * 100
        ).fillna(0.0)
        return result
