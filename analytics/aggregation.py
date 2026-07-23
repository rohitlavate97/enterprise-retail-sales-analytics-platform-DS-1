"""GroupBy / Agg / Transform sales aggregation analytics.

Business Questions Answered:
- What is total revenue, profit, and average order value per store?
- What is total revenue and unit volume per product category?
- How does each order compare to its store's average (transform)?
"""

import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)


class SalesAggregator:
    """GroupBy-based sales aggregation engine."""

    @staticmethod
    def aggregate_by_store(orders: pd.DataFrame) -> pd.DataFrame:
        """Aggregate sales KPIs per store.

        Business question: *Which stores drive the most revenue
        and profit, and what is their average order value?*

        Uses: ``groupby`` + ``agg`` with named aggregation.

        Args:
            orders: Orders fact table.

        Returns:
            DataFrame indexed by store_id with aggregated KPIs.
        """
        logger.info("Aggregating sales by store_id...")
        result = (
            orders.groupby("store_id", observed=True)
            .agg(
                total_revenue=("total_amount", "sum"),
                total_profit=("profit_amount", "sum"),
                total_cost=("cost_amount", "sum"),
                total_orders=("order_id", "count"),
                avg_quantity=("quantity", "mean"),
                avg_unit_price=("unit_price", "mean"),
            )
            .assign(
                avg_order_value=lambda df: df["total_revenue"]
                / df["total_orders"],
                profit_margin_pct=lambda df: (
                    df["total_profit"] / df["total_revenue"]
                )
                * 100,
            )
            .sort_values("total_revenue", ascending=False)
        )
        return result

    @staticmethod
    def aggregate_by_category(
        orders: pd.DataFrame,
        products: pd.DataFrame,
        categories: pd.DataFrame,
    ) -> pd.DataFrame:
        """Aggregate sales KPIs per product category.

        Business question: *Which product categories generate the
        most revenue and move the most units?*

        Uses: ``merge`` + ``groupby`` + ``agg``.

        Args:
            orders: Orders fact table.
            products: Products dimension table.
            categories: Categories dimension table.

        Returns:
            DataFrame indexed by category_name with aggregated KPIs.
        """
        logger.info("Aggregating sales by product category...")
        enriched = orders.merge(
            products[["product_id", "category_id"]],
            on="product_id",
            how="left",
        ).merge(
            categories[["category_id", "category_name"]],
            on="category_id",
            how="left",
        )
        result = (
            enriched.groupby("category_name", observed=True)
            .agg(
                total_revenue=("total_amount", "sum"),
                total_units=("quantity", "sum"),
                total_orders=("order_id", "count"),
                avg_order_value=(
                    "total_amount",
                    "mean",
                ),
            )
            .sort_values("total_revenue", ascending=False)
        )
        return result

    @staticmethod
    def store_deviation_transform(
        orders: pd.DataFrame,
    ) -> pd.DataFrame:
        """Add per-order deviation from store average revenue.

        Business question: *How does each individual order compare
        to its store's average order value?*

        Uses: ``groupby`` + ``transform`` to broadcast group
        statistics back to each row.

        Args:
            orders: Orders fact table.

        Returns:
            Original DataFrame with added columns:
            ``store_avg_revenue`` and ``revenue_vs_store_avg``.
        """
        logger.info(
            "Computing per-order store deviation via transform..."
        )
        result = orders.copy()
        result["store_avg_revenue"] = orders.groupby(
            "store_id", observed=True
        )["total_amount"].transform("mean")
        result["revenue_vs_store_avg"] = (
            result["total_amount"] - result["store_avg_revenue"]
        )
        return result
