"""Pivot table analytics for cross-dimensional sales matrices.

Business Questions Answered:
- What is the revenue breakdown by region AND product category?
- Which region-category combinations are under/over-performing?
- What percentage of each region's revenue comes from each category?
"""

import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)


class PivotAnalytics:
    """Pivot-table based cross-dimensional analysis engine."""

    @staticmethod
    def region_by_category_revenue(
        orders: pd.DataFrame,
        products: pd.DataFrame,
        categories: pd.DataFrame,
        stores: pd.DataFrame,
        regions: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build region × category revenue pivot matrix.

        Business question: *What is the revenue distribution
        across regions and product categories?*

        Uses: ``pd.pivot_table`` with ``aggfunc='sum'``.

        Args:
            orders: Orders fact table.
            products: Products dimension (product_id → category_id).
            categories: Categories dimension (category_id → name).
            stores: Stores dimension (store_id → region_id).
            regions: Regions dimension (region_id → region_name).

        Returns:
            Pivot DataFrame with regions as rows and categories
            as columns, values = total revenue.
        """
        logger.info("Building region × category revenue pivot...")
        enriched = (
            orders.merge(
                products[["product_id", "category_id"]],
                on="product_id",
                how="left",
            )
            .merge(
                categories[["category_id", "category_name"]],
                on="category_id",
                how="left",
            )
            .merge(
                stores[["store_id", "region_id"]],
                on="store_id",
                how="left",
            )
            .merge(
                regions[["region_id", "region_name"]],
                on="region_id",
                how="left",
            )
        )
        pivot = pd.pivot_table(
            enriched,
            values="total_amount",
            index="region_name",
            columns="category_name",
            aggfunc="sum",
            fill_value=0,
        )
        return pivot

    @staticmethod
    def region_category_share(
        pivot: pd.DataFrame,
    ) -> pd.DataFrame:
        """Compute each category's % share of regional revenue.

        Business question: *What percentage of each region's
        revenue comes from each product category?*

        Uses: ``div`` with ``axis=0`` for row-wise normalisation.

        Args:
            pivot: Region × category revenue pivot table.

        Returns:
            DataFrame of the same shape with percentage values.
        """
        logger.info("Computing category share per region...")
        row_totals = pivot.sum(axis=1)
        share = pivot.div(row_totals, axis=0) * 100
        return share.round(2)

    @staticmethod
    def region_by_category_profit(
        orders: pd.DataFrame,
        products: pd.DataFrame,
        categories: pd.DataFrame,
        stores: pd.DataFrame,
        regions: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build region × category profit margin pivot matrix.

        Business question: *Which region-category combinations
        have the highest / lowest profit margins?*

        Uses: ``pd.pivot_table`` with custom ``aggfunc``.

        Args:
            orders: Orders fact table.
            products: Products dimension.
            categories: Categories dimension.
            stores: Stores dimension.
            regions: Regions dimension.

        Returns:
            Pivot DataFrame with margin percentages.
        """
        logger.info(
            "Building region × category profit margin pivot..."
        )
        enriched = (
            orders.merge(
                products[["product_id", "category_id"]],
                on="product_id",
                how="left",
            )
            .merge(
                categories[["category_id", "category_name"]],
                on="category_id",
                how="left",
            )
            .merge(
                stores[["store_id", "region_id"]],
                on="store_id",
                how="left",
            )
            .merge(
                regions[["region_id", "region_name"]],
                on="region_id",
                how="left",
            )
        )

        # Aggregate both revenue and profit, then compute margin
        agg = (
            enriched.groupby(
                ["region_name", "category_name"], observed=True
            )
            .agg(
                revenue=("total_amount", "sum"),
                profit=("profit_amount", "sum"),
            )
            .reset_index()
        )
        agg["margin_pct"] = (agg["profit"] / agg["revenue"]) * 100

        pivot = agg.pivot(
            index="region_name",
            columns="category_name",
            values="margin_pct",
        ).fillna(0)
        return pivot.round(2)
