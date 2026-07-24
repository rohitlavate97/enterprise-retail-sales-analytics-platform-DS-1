"""Time-series and resampling analysis engine.

Business Questions Answered:
- What are the monthly and weekly trends in revenue, profit, and orders?
- Is there a clear seasonal pattern?
"""

import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)


class TemporalAnalytics:
    """Time-series and resampling analysis engine using Pandas."""

    @staticmethod
    def resample_sales(
        orders: pd.DataFrame,
        time_dim: pd.DataFrame,
        rule: str = "ME",
    ) -> pd.DataFrame:
        """Resample sales metrics to a given frequency (e.g., monthly, weekly).

        Business question: *What are the monthly or weekly trends in revenue, profit,
        and order volumes, and how do they compare over time?*

        Uses: ``merge`` + ``resample`` on a DatetimeIndex.

        Args:
            orders: Orders fact table.
            time_dim: Time dimension calendar table.
            rule: Resampling frequency rule (e.g., 'ME' for month-end, 'W' for weekly).

        Returns:
            DataFrame indexed by the resampled date with aggregated metrics.
        """
        logger.info("Resampling sales analytics using rule: %s...", rule)

        # Merge orders with time dimension to get the calendar dates
        enriched = orders.merge(
            time_dim[["date_key", "full_date"]],
            on="date_key",
            how="left",
        )

        # Ensure full_date is parsed as datetime
        enriched["full_date"] = pd.to_datetime(enriched["full_date"])

        # Resample and aggregate
        resampled = (
            enriched.set_index("full_date")
            .resample(rule)
            .agg(
                total_revenue=("total_amount", "sum"),
                total_profit=("profit_amount", "sum"),
                total_orders=("order_id", "count"),
                units_sold=("quantity", "sum"),
            )
        )

        # Calculate derived KPIs with safe division
        resampled["avg_order_value"] = (
            resampled["total_revenue"] / resampled["total_orders"]
        ).fillna(0.0)

        resampled["profit_margin_pct"] = (
            (resampled["total_profit"] / resampled["total_revenue"]) * 100
        ).fillna(0.0)

        logger.info("Resampling complete. Resulting shape: %s", resampled.shape)
        return resampled
